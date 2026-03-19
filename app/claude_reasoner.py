"""
claude_reasoner.py
Alternative reasoner that calls the Anthropic Claude API directly
instead of OpenRouter. Used for agentic reasoning with tool-use support.
"""

import json
import os
from typing import Any, Dict, List, Optional

import requests

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def convert_numpy_types(obj: Any) -> Any:
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    try:
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
    except ImportError:
        pass
    return obj


def build_diagnostic_prompt(
    findings: List[Dict],
    asset_name: str,
    risk_profile: Optional[Dict] = None,
    asset_history: Optional[List[Dict]] = None,
    stats: Optional[Dict] = None,
) -> str:
    """
    Build a rich user prompt for the diagnostic report, injecting
    findings, risk profile, asset history, and sensor statistics.
    """
    clean_findings = convert_numpy_types(findings)

    sections = [f"Asset: {asset_name}\n"]

    if stats:
        sections.append(
            f"Sensor Statistics:\n{json.dumps(stats, indent=2)}\n"
        )

    if risk_profile:
        sections.append(
            f"Risk Profile:\n{json.dumps(risk_profile, indent=2)}\n"
        )

    if asset_history:
        sections.append(
            f"Past Session History ({len(asset_history)} sessions):\n"
            + json.dumps(asset_history, indent=2, default=str)
            + "\n"
        )

    sections.append(
        f"Anomaly Findings ({len(clean_findings)} total):\n"
        + json.dumps(clean_findings, indent=2)
    )

    sections.append(
        """
Generate a structured diagnostic report with these exact sections:

Issue Detected:
Evidence:
Likely Root Causes:
Severity:
Recommended Actions:
Confidence:
Additional Data Needed:
"""
    )

    return "\n".join(sections)


def call_claude_api(
    messages: List[Dict],
    system_prompt: str,
    max_tokens: int = 1500,
) -> str:
    """
    Call the Anthropic Claude API and return the assistant's text response.
    Raises an exception if the API key is missing or the call fails.
    """
    if not ANTHROPIC_API_KEY:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file to use the Claude reasoner."
        )

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
    }

    response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"Anthropic API error {response.status_code}: {response.text}"
        )

    data = response.json()
    content_blocks = data.get("content", [])
    text = " ".join(
        block["text"] for block in content_blocks if block.get("type") == "text"
    )
    return text.strip()


def generate_diagnostic_report_claude(
    findings: List[Dict],
    asset_name: str,
    system_prompt: str,
    risk_profile: Optional[Dict] = None,
    asset_history: Optional[List[Dict]] = None,
    sensor_stats: Optional[Dict] = None,
) -> str:
    """
    Generate an AI diagnostic report using the Claude API directly.
    This is richer than the OpenRouter path because it injects risk profile
    and historical context into the prompt.
    """
    user_prompt = build_diagnostic_prompt(
        findings=findings,
        asset_name=asset_name,
        risk_profile=risk_profile,
        asset_history=asset_history,
        stats=sensor_stats,
    )

    messages = [{"role": "user", "content": user_prompt}]
    return call_claude_api(messages, system_prompt=system_prompt)


def multi_turn_reasoning(
    conversation_history: List[Dict],
    system_prompt: str,
    new_user_message: str,
) -> str:
    """
    Continue a multi-turn conversation with Claude.
    Useful for follow-up questions after the initial diagnostic report.

    Args:
        conversation_history: list of {"role": ..., "content": ...} dicts
        system_prompt: the agent's system prompt
        new_user_message: the new message to append

    Returns:
        Claude's response text
    """
    messages = conversation_history + [
        {"role": "user", "content": new_user_message}
    ]
    return call_claude_api(messages, system_prompt=system_prompt)
