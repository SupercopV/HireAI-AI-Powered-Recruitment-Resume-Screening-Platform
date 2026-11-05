from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ScoreEvidenceResponse(BaseModel):
    id: int
    criterion_name: str
    max_score: float
    awarded_score: float
    evidence_quote: str
    explanation: str
    missing_info: Optional[str] = None

    class Config:
        from_attributes = True


class CandidateScoreResponse(BaseModel):
    id: int
    candidate_id: int
    requisition_id: int
    scorecard_id: int
    total_score: float
    max_possible_score: float
    required_skills_score: float
    experience_score: float
    relevant_experience_score: float
    good_to_have_score: float
    notice_period_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    match_grade: str
    ai_reasoning: Optional[str]
    is_demo_score: bool
    created_at: datetime
    evidence_items: List[ScoreEvidenceResponse] = []

    class Config:
        from_attributes = True


class ScoreCalculationRequest(BaseModel):
    requisition_id: int
    override_weights: Optional[Dict[str, float]] = None

