import json
import requests
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL


def convert_numpy_types(obj):

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
    except:
        pass

    return obj


def build_reasoning_prompt(findings, asset_name):

    clean = convert_numpy_types(findings)

    return f"""
Asset: {asset_name}

Sensor anomaly findings:

{json.dumps(clean, indent=2)}

Generate a troubleshooting report.

Format:

Issue Detected:
Evidence:
Likely Root Causes:
Severity:
Recommended Actions:
Confidence:
Additional Data Needed:
"""


def generate_diagnostic_report(findings, asset_name="Unknown Asset"):

    if not OPENROUTER_API_KEY:
        raise Exception("OPENROUTER_API_KEY missing")

    with open("prompts/system_prompt.txt") as f:
        system_prompt = f.read()

    user_prompt = build_reasoning_prompt(findings, asset_name)

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/indusdiag",
            "X-Title": "IndusDiag"
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
    )

    result = response.json()

    if "choices" not in result:
        raise Exception(f"OpenRouter error: {result}")

    return result["choices"][0]["message"]["content"]