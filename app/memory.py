"""
memory.py
Provides short-term (session) and long-term (file-backed) memory for the IndusDiag agent.

Short-term memory: holds findings and reports from the current run in RAM.
Long-term memory: persists sessions to a local JSON file for historical lookup.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


MEMORY_FILE = "data/memory/agent_memory.json"


# ---------------------------------------------------------------------------
# Short-term (in-process) session memory
# ---------------------------------------------------------------------------

class SessionMemory:
    """
    Holds state for a single agent run.
    The agent uses this to maintain context across tool calls within one session.
    """

    def __init__(self, asset_name: str):
        self.asset_name = asset_name
        self.started_at: str = datetime.now().isoformat()
        self.parsed_data = None          # pd.DataFrame after parsing
        self.raw_findings: List[Dict] = []
        self.scored_findings: List[Dict] = []
        self.risk_profile: Dict[str, Any] = {}
        self.diagnostic_report: Optional[str] = None
        self.tool_call_log: List[Dict] = []  # tracks every tool the agent called
        self.messages: List[Dict] = []       # full conversation history for LLM

    def log_tool_call(self, tool_name: str, args: Dict, result: Any):
        self.tool_call_log.append({
            "tool": tool_name,
            "args": args,
            "result_summary": str(result)[:300],
            "timestamp": datetime.now().isoformat(),
        })

    def add_message(self, role: str, content: str):
        """Append a message to the conversation history."""
        self.messages.append({"role": role, "content": content})

    def to_summary(self) -> Dict[str, Any]:
        return {
            "asset_name": self.asset_name,
            "timestamp": self.started_at,
            "finding_count": len(self.raw_findings),
            "risk_level": self.risk_profile.get("risk_level", "UNKNOWN"),
            "dominant_issue": self.risk_profile.get("dominant_issue"),
            "tool_calls": len(self.tool_call_log),
        }


# ---------------------------------------------------------------------------
# Long-term (file-backed) persistent memory
# ---------------------------------------------------------------------------

class PersistentMemory:
    """
    Reads and writes session summaries to a local JSON file.
    Allows the agent to recall past diagnoses for an asset.
    """

    def __init__(self, path: str = MEMORY_FILE):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._data: Dict[str, List[Dict]] = self._load()

    def _load(self) -> Dict[str, List[Dict]]:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    def save_session(self, session: SessionMemory):
        """Persist a completed session summary for the asset."""
        asset = session.asset_name
        if asset not in self._data:
            self._data[asset] = []
        self._data[asset].append(session.to_summary())
        self._save()

    def get_history(self, asset_name: str, limit: int = 10) -> List[Dict]:
        """Return the last N sessions for a given asset."""
        return self._data.get(asset_name, [])[-limit:]

    def get_all_assets(self) -> List[str]:
        """Return all asset names that have memory entries."""
        return list(self._data.keys())

    def get_trend(self, asset_name: str) -> str:
        """
        Simple trend summary: are findings increasing or decreasing over time?
        """
        history = self.get_history(asset_name)
        if len(history) < 2:
            return "Not enough history to determine trend."

        counts = [h["finding_count"] for h in history]
        if counts[-1] > counts[-2]:
            return f"⚠️  Findings increasing: {counts[-2]} → {counts[-1]}"
        elif counts[-1] < counts[-2]:
            return f"✅  Findings decreasing: {counts[-2]} → {counts[-1]}"
        else:
            return f"➡️  Findings stable at {counts[-1]}"

    def find_similar_past_issues(
        self, asset_name: str, issue_type: str
    ) -> List[Dict]:
        """Return past sessions for this asset that had the same dominant issue."""
        history = self.get_history(asset_name)
        return [h for h in history if h.get("dominant_issue") == issue_type]
