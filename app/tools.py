"""
tools.py
Defines callable tools for the IndusDiag agent.

Each tool is a plain function the agent can invoke.
The TOOLS registry maps tool names → callables + metadata for the LLM.
"""

from typing import Any, Dict, List, Optional
import json
import pandas as pd

from app.detector import (
    detect_spike,
    detect_flatline,
    detect_missing_data,
    detect_out_of_range,
    detect_drift,
    detect_pump_cavitation,
)
from app.scorer import compute_asset_risk, score_all_findings
from app.formatter import format_findings_table, format_summary_stats


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def tool_run_spike_detector(df: pd.DataFrame, threshold: float = 50) -> Dict:
    findings = detect_spike(df, threshold=threshold)
    return {
        "tool": "run_spike_detector",
        "findings": findings,
        "count": len(findings),
        "summary": f"Found {len(findings)} spike(s) with threshold={threshold}",
    }


def tool_run_flatline_detector(df: pd.DataFrame, window: int = 5) -> Dict:
    findings = detect_flatline(df, window=window)
    return {
        "tool": "run_flatline_detector",
        "findings": findings,
        "count": len(findings),
        "summary": f"Found {len(findings)} flatline(s) with window={window}",
    }


def tool_run_missing_data_detector(
    df: pd.DataFrame, expected_interval_minutes: int = 1
) -> Dict:
    findings = detect_missing_data(df, expected_interval_minutes)
    return {
        "tool": "run_missing_data_detector",
        "findings": findings,
        "count": len(findings),
        "summary": f"Found {len(findings)} data gap(s)",
    }


def tool_run_out_of_range_detector(
    df: pd.DataFrame, min_val: float = 0, max_val: float = 200
) -> Dict:
    findings = detect_out_of_range(df, min_val=min_val, max_val=max_val)
    return {
        "tool": "run_out_of_range_detector",
        "findings": findings,
        "count": len(findings),
        "summary": f"Found {len(findings)} out-of-range value(s) in [{min_val}, {max_val}]",
    }


def tool_run_drift_detector(df: pd.DataFrame, window: int = 5) -> Dict:
    findings = detect_drift(df, window=window)
    return {
        "tool": "run_drift_detector",
        "findings": findings,
        "count": len(findings),
        "summary": f"Found {len(findings)} drift event(s)",
    }


def tool_run_pump_cavitation_detector(
    df: pd.DataFrame,
    window: int = 10,
    low_factor: float = 0.8,
    oscillations_threshold: int = 3,
    amplitude_min_pct: float = 0.05,
) -> Dict:
    findings = detect_pump_cavitation(
        df,
        window=window,
        low_factor=low_factor,
        oscillations_threshold=oscillations_threshold,
        amplitude_min_pct=amplitude_min_pct,
    )
    return {
        "tool": "run_pump_cavitation_detector",
        "findings": findings,
        "count": len(findings),
        "summary": (
            f"Found {len(findings)} pump cavitation suspect event(s) "
            f"(window={window}, low_factor={low_factor}, "
            f"oscillations>={oscillations_threshold})"
        ),
    }


def tool_compute_risk(findings: List[Dict]) -> Dict:
    risk = compute_asset_risk(findings)
    return {
        "tool": "compute_risk",
        "risk_profile": risk,
        "summary": (
            f"Risk level: {risk['risk_level']} "
            f"(score={risk['risk_score']:.2f}), "
            f"dominant issue: {risk['dominant_issue']}"
        ),
    }


def tool_get_value_statistics(df: pd.DataFrame) -> Dict:
    """Return basic statistics of the sensor value column."""
    stats = df["value"].describe().to_dict()
    return {
        "tool": "get_value_statistics",
        "stats": {k: round(v, 3) for k, v in stats.items()},
        "summary": (
            f"mean={stats['mean']:.2f}, std={stats['std']:.2f}, "
            f"min={stats['min']:.2f}, max={stats['max']:.2f}"
        ),
    }


def tool_get_asset_history(
    memory, asset_name: str, limit: int = 5
) -> Dict:
    """Retrieve past session summaries from persistent memory."""
    history = memory.get_history(asset_name, limit=limit)
    trend = memory.get_trend(asset_name)
    return {
        "tool": "get_asset_history",
        "history": history,
        "trend": trend,
        "summary": f"Found {len(history)} past session(s). Trend: {trend}",
    }


def tool_get_similar_past_issues(
    memory, asset_name: str, issue_type: str
) -> Dict:
    """Find past sessions with the same dominant issue type."""
    matches = memory.find_similar_past_issues(asset_name, issue_type)
    return {
        "tool": "get_similar_past_issues",
        "matches": matches,
        "count": len(matches),
        "summary": f"Found {len(matches)} past session(s) with dominant issue '{issue_type}'",
    }


def tool_filter_findings_by_type(
    findings: List[Dict], issue_type: str
) -> Dict:
    """Filter findings to only those of a specific type."""
    filtered = [f for f in findings if f.get("issue_type") == issue_type]
    return {
        "tool": "filter_findings_by_type",
        "findings": filtered,
        "count": len(filtered),
        "summary": f"Filtered to {len(filtered)} finding(s) of type '{issue_type}'",
    }


def tool_format_findings_report(findings: List[Dict]) -> Dict:
    """Format findings into a human-readable text table."""
    table = format_findings_table(findings)
    stats = format_summary_stats(findings)
    return {
        "tool": "format_findings_report",
        "formatted_table": table,
        "stats": stats,
        "summary": f"Formatted {len(findings)} finding(s) into report",
    }


# ---------------------------------------------------------------------------
# Tool registry — what the agent knows about each tool
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "run_spike_detector",
        "description": "Detect sudden spike anomalies in sensor values. Use when values jump sharply.",
        "parameters": {"threshold": "float (default 50) — minimum change to be called a spike"},
    },
    {
        "name": "run_flatline_detector",
        "description": "Detect flatline (stuck sensor) anomalies. Use when values stop changing.",
        "parameters": {"window": "int (default 5) — number of identical consecutive readings"},
    },
    {
        "name": "run_missing_data_detector",
        "description": "Detect gaps in the time series. Use when timestamps are irregular.",
        "parameters": {"expected_interval_minutes": "int (default 1)"},
    },
    {
        "name": "run_out_of_range_detector",
        "description": "Detect values outside safe operating bounds. Always run this.",
        "parameters": {"min_val": "float (default 0)", "max_val": "float (default 200)"},
    },
    {
        "name": "run_drift_detector",
        "description": "Detect gradual upward drift over time. Use for temperature or pressure sensors.",
        "parameters": {"window": "int (default 5) — rolling window size"},
    },
    {
        "name": "run_pump_cavitation_detector",
        "description": (
            "Detect pump cavitation (oscillatory behavior with a drop below a "
            "rolling baseline). Use when the sensor shows repeated low-pressure "
            "oscillations."
        ),
        "parameters": {
            "window": "int (default 10) — rolling window size",
            "low_factor": (
                "float (default 0.8) — current must be <= baseline * low_factor"
            ),
            "oscillations_threshold": (
                "int (default 3) — required sign flips in first differences"
            ),
            "amplitude_min_pct": (
                "float (default 0.05) — minimum amplitude relative to baseline"
            ),
        },
    },
    {
        "name": "compute_risk",
        "description": "Compute overall asset risk score and severity level from all findings.",
        "parameters": {},
    },
    {
        "name": "get_value_statistics",
        "description": "Get descriptive statistics (mean, std, min, max) of the sensor readings.",
        "parameters": {},
    },
    {
        "name": "get_asset_history",
        "description": "Retrieve past session history for this asset from memory.",
        "parameters": {"limit": "int (default 5) — number of past sessions to retrieve"},
    },
    {
        "name": "get_similar_past_issues",
        "description": "Find past sessions for this asset with the same dominant issue type.",
        "parameters": {"issue_type": "str — the issue type to search for"},
    },
    {
        "name": "filter_findings_by_type",
        "description": "Filter the findings list to a specific issue type for focused analysis.",
        "parameters": {"issue_type": "str"},
    },
    {
        "name": "format_findings_report",
        "description": "Format all findings into a structured human-readable table.",
        "parameters": {},
    },
]


def get_tool_descriptions() -> str:
    """Return a formatted string of all tool names + descriptions for the system prompt."""
    lines = []
    for t in TOOL_DEFINITIONS:
        params = ", ".join(
            f"{k}: {v}" for k, v in t["parameters"].items()
        ) or "none"
        lines.append(f"- {t['name']}: {t['description']} | params: {params}")
    return "\n".join(lines)
