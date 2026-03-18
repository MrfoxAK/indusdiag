from typing import List
from pydantic import BaseModel


class AnomalyFinding(BaseModel):
    issue_type: str
    index: int
    value: float | None = None
    message: str


class DiagnosticReport(BaseModel):
    issue_detected: str
    evidence: List[str]
    likely_root_causes: List[str]
    severity: str
    recommended_actions: List[str]
    confidence: float
    additional_data_needed: List[str]