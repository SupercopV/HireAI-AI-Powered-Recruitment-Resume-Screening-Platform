from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ScoringWeights(BaseModel):
    required_skills: float = 40.0
    experience_match: float = 25.0
    relevant_experience: float = 15.0
    good_to_have_skills: float = 10.0
    notice_period: float = 10.0


class JDAnalysisRequest(BaseModel):
    job_description_text: str = Field(..., min_length=20, description="Full job description text to analyze")
    job_title: Optional[str] = None


class JDAnalysisResponse(BaseModel):
    must_have_skills: List[str]
    good_to_have_skills: List[str]
    min_experience: float
    max_experience: float
    location: str
    max_notice_period: int
    ctc_info: str
    suggested_title: Optional[str] = None
    summary: Optional[str] = None


class ScorecardBase(BaseModel):
    must_have_skills: List[str] = []
    good_to_have_skills: List[str] = []
    min_experience: float = 0.0
    max_experience: float = 10.0
    location: str = "Noida"
    max_notice_period: int = 60
    ctc_info: str = ""
    weights: Dict[str, float] = {
        "required_skills": 40.0,
        "experience_match": 25.0,
        "relevant_experience": 15.0,
        "good_to_have_skills": 10.0,
        "notice_period": 10.0
    }
    is_approved: bool = False


class ScorecardUpdate(ScorecardBase):
    pass


class ScorecardResponse(ScorecardBase):
    id: int
    requisition_id: int
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequisitionBase(BaseModel):
    title: str
    department: str = "Engineering"
    location: str = "Noida"
    experience_min: float = 0.0
    experience_max: float = 10.0
    ctc_min_lpa: float = 0.0
    ctc_max_lpa: float = 0.0
    employment_type: str = "Full-Time"
    max_notice_period_days: int = 60
    description: str


class RequisitionCreate(RequisitionBase):
    client_org_id: Optional[int] = None


class RequisitionUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    ctc_min_lpa: Optional[float] = None
    ctc_max_lpa: Optional[float] = None
    employment_type: Optional[str] = None
    max_notice_period_days: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None
    client_org_id: Optional[int] = None


class RequisitionResponse(RequisitionBase):
    id: int
    requisition_code: str
    status: str
    client_org_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    scorecards: List[ScorecardResponse] = []
    candidates_count: Optional[int] = 0

    class Config:
        from_attributes = True

