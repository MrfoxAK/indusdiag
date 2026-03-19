"""
scorer.py
Scores anomaly findings by severity and produces a risk summary for the agent.
"""

from typing import List, Dict, Any


# Weight per issue type (higher = more severe)
ISSUE_WEIGHTS: Dict[str, float] = {
    "out_of_range": 1.0,
    "sensor_spike": 0.8,
    "missing_data": 0.6,
    "drift": 0.5,
    "flatline": 0.4,
}

# Severity thresholds based on weighted score
SEVERITY_THRESHOLDS = [
    (0.8, "CRITICAL"),
    (0.6, "HIGH"),
    (0.4, "MEDIUM"),
    (0.2, "LOW"),
    (0.0, "INFO"),
]


def score_finding(finding: Dict[str, Any]) -> float:
    """Return a 0.0–1.0 severity score for a single finding."""
    issue_type = finding.get("issue_type", "unknown")
    base_score = ISSUE_WEIGHTS.get(issue_type, 0.3)

    # Boost score if value is present and extreme
    value = finding.get("value")
    if isinstance(value, (int, float)):
        if value > 500 or value < -100:
            base_score = min(base_score + 0.2, 1.0)

    return round(base_score, 3)


def classify_severity(score: float) -> str:
    """Map a score to a severity label."""
    for threshold, label in SEVERITY_THRESHOLDS:
        if score >= threshold:
            return label
    return "INFO"


def score_all_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Attach a score and severity to each finding."""
    scored = []
    for f in findings:
        f = dict(f)  # don't mutate original
        score = score_finding(f)
        f["score"] = score
        f["severity"] = classify_severity(score)
        scored.append(f)
    return scored


def compute_asset_risk(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute an overall risk profile for the asset based on all findings.
    Returns a dict with risk_score, risk_level, dominant_issue, and finding_count.
    """
    if not findings:
        return {
            "risk_score": 0.0,
            "risk_level": "NONE",
            "dominant_issue": None,
            "finding_count": 0,
        }

    scored = score_all_findings(findings)
    scores = [f["score"] for f in scored]

    # Weighted aggregate: max score + mean as a blend
    max_score = max(scores)
    mean_score = sum(scores) / len(scores)
    aggregate = round((max_score * 0.6) + (mean_score * 0.4), 3)

    # Find dominant issue type
    issue_counts: Dict[str, int] = {}
    for f in findings:
        t = f.get("issue_type", "unknown")
        issue_counts[t] = issue_counts.get(t, 0) + 1
    dominant = max(issue_counts, key=lambda k: issue_counts[k])

    return {
        "risk_score": aggregate,
        "risk_level": classify_severity(aggregate),
        "dominant_issue": dominant,
        "finding_count": len(findings),
        "issue_breakdown": issue_counts,
    }


def score_report_confidence(findings: List[Dict[str, Any]], report_text: str) -> float:
    """
    Heuristic: estimate how confident the AI report is based on
    finding count and report length.
    """
    if not findings or not report_text:
        return 0.0

    base = min(len(findings) / 20.0, 0.5)        # more findings → more data
    text_factor = min(len(report_text) / 2000.0, 0.5)  # longer report → more detail
    return round(base + text_factor, 3)
