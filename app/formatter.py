"""
formatter.py
Formats anomaly findings and diagnostic reports for terminal display and file output.
"""

from typing import List, Dict, Any
from datetime import datetime


SEVERITY_COLORS = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "cyan",
    "info": "dim",
}

ISSUE_ICONS = {
    "sensor_spike": "⚡",
    "flatline": "📉",
    "missing_data": "🕳️",
    "out_of_range": "🚨",
    "drift": "📈",
    "pump_cavitation": "🫧",
    "unknown": "❓",
}


def format_finding(finding: Dict[str, Any]) -> str:
    """Format a single finding dict into a readable string."""
    issue_type = finding.get("issue_type", "unknown")
    icon = ISSUE_ICONS.get(issue_type, ISSUE_ICONS["unknown"])
    index = finding.get("index", "N/A")
    value = finding.get("value", "N/A")
    message = finding.get("message", "No message")

    value_str = f" | value={value:.2f}" if isinstance(value, (int, float)) else ""
    return f"{icon}  [{issue_type.upper()}] idx={index}{value_str} → {message}"


def format_findings_table(findings: List[Dict[str, Any]]) -> str:
    """Format all findings as a structured text table."""
    if not findings:
        return "✅  No anomalies detected."

    lines = []
    lines.append("=" * 70)
    lines.append(f"  ANOMALY FINDINGS  ({len(findings)} total)")
    lines.append("=" * 70)

    grouped: Dict[str, List] = {}
    for f in findings:
        issue_type = f.get("issue_type", "unknown")
        grouped.setdefault(issue_type, []).append(f)

    for issue_type, items in grouped.items():
        icon = ISSUE_ICONS.get(issue_type, ISSUE_ICONS["unknown"])
        lines.append(f"\n{icon}  {issue_type.upper()}  ({len(items)} occurrences)")
        lines.append("-" * 50)
        for item in items[:5]:  # cap display at 5 per type
            lines.append(f"   {format_finding(item)}")
        if len(items) > 5:
            lines.append(f"   ... and {len(items) - 5} more")

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)


def format_summary_stats(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return a count breakdown by issue type."""
    stats: Dict[str, int] = {}
    for f in findings:
        issue_type = f.get("issue_type", "unknown")
        stats[issue_type] = stats.get(issue_type, 0) + 1
    return stats


def format_report_header(asset_name: str) -> str:
    """Generate a report header with timestamp."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"\n{'=' * 70}\n"
        f"  AI DIAGNOSTIC REPORT\n"
        f"  Asset: {asset_name}\n"
        f"  Generated: {now}\n"
        f"{'=' * 70}\n"
    )


def format_memory_context(memory_entries: List[Dict[str, Any]]) -> str:
    """Format past session memory entries for display."""
    if not memory_entries:
        return "No previous sessions found."

    lines = ["📚  SESSION HISTORY"]
    for i, entry in enumerate(memory_entries[-5:], 1):  # last 5
        ts = entry.get("timestamp", "unknown time")
        asset = entry.get("asset_name", "unknown asset")
        count = entry.get("finding_count", 0)
        lines.append(f"  [{i}] {ts} | Asset: {asset} | Findings: {count}")
    return "\n".join(lines)
