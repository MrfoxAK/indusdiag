"""
agent.py
The core IndusDiag Agent.

This agent:
1. Parses sensor data
2. Runs all detectors via tools
3. Scores and ranks findings
4. Retrieves asset history from memory
5. Generates an AI diagnostic report (Claude or OpenRouter)
6. Saves the session to persistent memory
7. Supports follow-up multi-turn Q&A

The agent maintains a tool call log and conversation history
for full observability.
"""

import os
from typing import Any, Dict, List, Optional

from rich import print as rprint
from rich.panel import Panel
from rich.table import Table

from app.parser import parse_sensor_data
from app.detector import run_all_detectors
from app.scorer import compute_asset_risk, score_all_findings
from app.memory import SessionMemory, PersistentMemory
from app.formatter import (
    format_findings_table,
    format_report_header,
    format_memory_context,
)
from app.tools import (
    tool_run_spike_detector,
    tool_run_flatline_detector,
    tool_run_missing_data_detector,
    tool_run_out_of_range_detector,
    tool_run_drift_detector,
    tool_compute_risk,
    tool_get_value_statistics,
    tool_get_asset_history,
    tool_get_similar_past_issues,
    tool_filter_findings_by_type,
    tool_format_findings_report,
    get_tool_descriptions,
)


SYSTEM_PROMPT_PATH = "prompts/system_prompt.txt"


def load_system_prompt() -> str:
    if os.path.exists(SYSTEM_PROMPT_PATH):
        with open(SYSTEM_PROMPT_PATH, "r") as f:
            return f.read()
    # Fallback inline prompt
    return (
        "You are IndusDiag, an expert AI agent for industrial sensor diagnostics. "
        "Analyze sensor anomalies and generate precise, actionable troubleshooting reports. "
        "Be concise, technical, and evidence-based. Always cite specific findings."
    )


class IndusDiagAgent:
    """
    The main agent class. Orchestrates parsing, detection, scoring,
    memory, and LLM-based reasoning in a structured agentic loop.
    """

    def __init__(
        self,
        asset_name: str,
        use_claude: bool = False,
        verbose: bool = True,
    ):
        self.asset_name = asset_name
        self.use_claude = use_claude
        self.verbose = verbose
        self.system_prompt = load_system_prompt()
        self.session = SessionMemory(asset_name)
        self.persistent_memory = PersistentMemory()

    # ------------------------------------------------------------------
    # Internal logging
    # ------------------------------------------------------------------

    def _log(self, msg: str):
        if self.verbose:
            rprint(msg)

    def _call_tool(self, tool_name: str, fn, *args, **kwargs) -> Any:
        """Invoke a tool, log the call, and return the result."""
        self._log(f"[dim]🔧 Tool: [cyan]{tool_name}[/cyan][/dim]")
        result = fn(*args, **kwargs)
        self.session.log_tool_call(tool_name, kwargs, result)
        return result

    # ------------------------------------------------------------------
    # Phase 1: Parse
    # ------------------------------------------------------------------

    def load_data(self, file_path: str):
        self._log(f"\n[bold blue]📂 Loading sensor data from:[/bold blue] {file_path}")
        df = parse_sensor_data(file_path)
        self.session.parsed_data = df
        self._log(f"[green]✅ Parsed {len(df)} rows[/green]")
        return df

    # ------------------------------------------------------------------
    # Phase 2: Tool-driven detection
    # ------------------------------------------------------------------

    def run_detection_tools(self) -> List[Dict]:
        """Run each detector as a named tool call."""
        df = self.session.parsed_data
        self._log("\n[bold yellow]🔍 Running detection tools...[/bold yellow]")

        all_findings = []

        r = self._call_tool("run_spike_detector", tool_run_spike_detector, df)
        all_findings += r["findings"]

        r = self._call_tool("run_flatline_detector", tool_run_flatline_detector, df)
        all_findings += r["findings"]

        r = self._call_tool("run_missing_data_detector", tool_run_missing_data_detector, df)
        all_findings += r["findings"]

        r = self._call_tool("run_out_of_range_detector", tool_run_out_of_range_detector, df)
        all_findings += r["findings"]

        r = self._call_tool("run_drift_detector", tool_run_drift_detector, df)
        all_findings += r["findings"]

        self.session.raw_findings = all_findings
        return all_findings

    # ------------------------------------------------------------------
    # Phase 3: Scoring + statistics
    # ------------------------------------------------------------------

    def run_scoring(self) -> Dict:
        """Score findings and compute risk profile."""
        self._log("\n[bold cyan]📊 Scoring findings...[/bold cyan]")

        findings = self.session.raw_findings

        r = self._call_tool("compute_risk", tool_compute_risk, findings)
        risk = r["risk_profile"]
        self.session.risk_profile = risk
        self._log(f"   Risk level: [bold]{risk['risk_level']}[/bold] (score={risk['risk_score']:.2f})")

        scored = score_all_findings(findings)
        self.session.scored_findings = scored

        stats_result = self._call_tool(
            "get_value_statistics", tool_get_value_statistics, self.session.parsed_data
        )
        return risk

    # ------------------------------------------------------------------
    # Phase 4: Memory lookup
    # ------------------------------------------------------------------

    def retrieve_memory(self) -> List[Dict]:
        """Pull past sessions for context."""
        self._log("\n[bold magenta]🧠 Retrieving asset memory...[/bold magenta]")

        r = self._call_tool(
            "get_asset_history",
            tool_get_asset_history,
            self.persistent_memory,
            self.asset_name,
        )
        history = r["history"]
        self._log(f"   {r['summary']}")

        # Also look for recurrence of dominant issue
        dominant = self.session.risk_profile.get("dominant_issue")
        if dominant:
            r2 = self._call_tool(
                "get_similar_past_issues",
                tool_get_similar_past_issues,
                self.persistent_memory,
                self.asset_name,
                dominant,
            )
            self._log(f"   {r2['summary']}")

        return history

    # ------------------------------------------------------------------
    # Phase 5: AI Diagnostic Report
    # ------------------------------------------------------------------

    def generate_report(self, asset_history: List[Dict]) -> str:
        """Call LLM to generate the diagnostic report."""
        self._log("\n[bold magenta]🤖 Generating AI diagnostic report...[/bold magenta]")

        findings = self.session.raw_findings
        risk = self.session.risk_profile

        if self.use_claude:
            from app.claude_reasoner import generate_diagnostic_report_claude

            # Pull stats from last tool call log
            stats = None
            for entry in reversed(self.session.tool_call_log):
                if entry["tool"] == "get_value_statistics":
                    import json
                    try:
                        result_data = entry["result_summary"]
                        # stored as string, so just pass None — stats are in prompt anyway
                    except Exception:
                        pass
                    break

            report = generate_diagnostic_report_claude(
                findings=findings,
                asset_name=self.asset_name,
                system_prompt=self.system_prompt,
                risk_profile=risk,
                asset_history=asset_history or None,
            )
        else:
            from app.reasoner import generate_diagnostic_report

            report = generate_diagnostic_report(
                findings=findings,
                asset_name=self.asset_name,
            )

        self.session.diagnostic_report = report
        self.session.add_message("user", f"Diagnose asset: {self.asset_name}")
        self.session.add_message("assistant", report)
        return report

    # ------------------------------------------------------------------
    # Phase 6: Save session to memory
    # ------------------------------------------------------------------

    def save_session(self):
        self.persistent_memory.save_session(self.session)
        self._log(
            f"\n[dim]💾 Session saved to memory for asset '{self.asset_name}'[/dim]"
        )

    # ------------------------------------------------------------------
    # Main orchestration
    # ------------------------------------------------------------------

    def run(self, file_path: str) -> str:
        """
        Full agentic pipeline:
        Parse → Detect → Score → Memory → Report → Save
        Returns the diagnostic report as a string.
        """
        self._log(
            Panel(
                f"[bold]IndusDiag Agent[/bold]\nAsset: [cyan]{self.asset_name}[/cyan]",
                expand=False,
            )
        )

        # Phase 1
        self.load_data(file_path)

        # Phase 2
        findings = self.run_detection_tools()

        # AFTER (sets a report so interactive Q&A still works):
        if not findings:
            self._log("\n[bold green]✅ No anomalies detected. Asset appears healthy.[/bold green]")
            self.session.diagnostic_report = "No anomalies were detected in this sensor data. The asset appears to be operating normally."
            self.session.add_message("assistant", self.session.diagnostic_report)
            self.save_session()
            return self.session.diagnostic_report

        # Phase 3
        self.run_scoring()

        # Phase 4
        history = self.retrieve_memory()

        # Display findings summary
        self._log("\n" + format_findings_table(findings))

        # Phase 5
        report = self.generate_report(history)

        # Display report
        self._log(format_report_header(self.asset_name))
        self._log(report)

        # Phase 6
        self.save_session()

        return report

    # ------------------------------------------------------------------
    # Multi-turn follow-up Q&A
    # ------------------------------------------------------------------

    def ask(self, question: str) -> str:
        """
        Ask a follow-up question about the diagnosis in the same session.
        Requires a report to have been generated first.
        """
        if not self.session.diagnostic_report:
            return "Please run a diagnosis first with agent.run(file_path)."

        if self.use_claude:
            from app.claude_reasoner import multi_turn_reasoning

            answer = multi_turn_reasoning(
                conversation_history=self.session.messages,
                system_prompt=self.system_prompt,
                new_user_message=question,
            )
        else:
            # For OpenRouter: rebuild context and re-call
            from app.reasoner import generate_diagnostic_report

            context_prompt = (
                f"Previous diagnosis for {self.asset_name}:\n\n"
                f"{self.session.diagnostic_report}\n\n"
                f"Follow-up question: {question}"
            )
            answer = generate_diagnostic_report(
                findings=[{"issue_type": "follow_up", "index": 0, "message": context_prompt}],
                asset_name=self.asset_name,
            )

        self.session.add_message("user", question)
        self.session.add_message("assistant", answer)

        if self.verbose:
            rprint(f"\n[bold cyan]Q:[/bold cyan] {question}")
            rprint(f"[bold green]A:[/bold green] {answer}")

        return answer
