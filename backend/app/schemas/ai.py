from datetime import datetime
from pydantic import BaseModel


class RiskScoreResponse(BaseModel):
    employee_id: str
    name: str
    score: int
    level: str
    reasoning: str
    recommendations: list[str]
    factors: dict
    calculated_at: datetime

    class Config:
        from_attributes = True


class BehaviorAnalysisResponse(BaseModel):
    employee_id: str
    name: str
    behavior_summary: str
    patterns: list[str]
    anomalies: list[dict]
    trends: list[dict]
    potential_causes: list[str]
    recommendations: list[str]
    confidence: str


class AIWarningResponse(BaseModel):
    employee_id: str
    name: str
    strike_level: int
    warning_type: str
    subject: str
    body: str
    tone: str


class ExecutiveReportResponse(BaseModel):
    id: str
    report_type: str
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportGenerateRequest(BaseModel):
    report_type: str = "weekly"
    department_id: str | None = None


class AIUsageSummary(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    by_feature: dict
