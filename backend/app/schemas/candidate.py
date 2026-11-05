from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class ResumeResponse(BaseModel):
    id: int
    candidate_id: Optional[int]
    requisition_id: Optional[int]
    file_name: str
    file_hash: str
    file_type: str
    file_size_bytes: int
    parsing_status: str
    parsing_error: Optional[str]
    ocr_applied: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    id: int
    batch_code: str
    requisition_id: int
    total_files: int
    parsed_count: int
    failed_count: int
    duplicate_count: int
    status: str
    created_at: datetime
    resumes: List[ResumeResponse] = []

    class Config:
        from_attributes = True


class CandidateBase(BaseModel):
    candidate_code: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_role: Optional[str] = None
    total_experience_years: float = 0.0
    relevant_experience_years: float = 0.0
    skills: List[str] = []
    notice_period_days: int = 30
    current_location: Optional[str] = ""
    education: Optional[str] = ""
    summary: Optional[str] = None


class CandidateCreate(CandidateBase):
    raw_text: Optional[str] = None


class CandidateUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_role: Optional[str] = None
    total_experience_years: Optional[float] = None
    relevant_experience_years: Optional[float] = None
    skills: Optional[List[str]] = None
    notice_period_days: Optional[int] = None
    current_location: Optional[str] = None
    education: Optional[str] = None
    summary: Optional[str] = None
    current_stage: Optional[str] = None


class CandidateResponse(CandidateBase):
    id: int
    current_stage: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    resumes: List[ResumeResponse] = []
    latest_score: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class CandidateMaskedResponse(BaseModel):
    """
    Masked candidate profile for Client Hiring Manager view.
    Masks personal contact info (email, phone, address) to maintain candidate privacy.
    """
    id: int
    candidate_code: str
    masked_name: str
    masked_email: str
    masked_phone: str
    current_role: Optional[str]
    total_experience_years: float
    skills: List[str]
    notice_period_days: int
    education: Optional[str]
    summary: Optional[str]
    current_stage: str
    created_at: datetime
    latest_score: Optional[Dict[str, Any]] = None
    submission_id: Optional[int] = None
    submission_status: Optional[str] = None
    recruiter_notes: Optional[str] = None

    class Config:
        from_attributes = True

