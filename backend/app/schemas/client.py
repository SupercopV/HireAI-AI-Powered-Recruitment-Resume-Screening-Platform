from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    requisition_id: int
    candidate_id: int
    client_org_id: int
    recruiter_notes: Optional[str] = None


class ClientShortlistRequest(BaseModel):
    feedback_text: Optional[str] = "Profile shortlisted for technical interview."


class ClientRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=3, description="Mandatory reason for rejection")
    feedback_text: Optional[str] = None


class ClientInterviewRequest(BaseModel):
    proposed_interview_time: datetime = Field(..., description="Proposed date and time for the interview")
    round_name: Optional[str] = "Technical Round 1"
    interviewer_name: Optional[str] = "Client Technical Lead"
    meeting_link: Optional[str] = None
    feedback_text: Optional[str] = None


class ClientFeedbackResponse(BaseModel):
    id: int
    action: str
    rejection_reason: Optional[str]
    feedback_text: Optional[str]
    proposed_interview_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewResponse(BaseModel):
    id: int
    submission_id: int
    round_name: str
    scheduled_time: datetime
    interviewer_name: str
    meeting_link: str
    status: str
    feedback: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ClientSubmissionResponse(BaseModel):
    id: int
    requisition_id: int
    candidate_id: int
    client_org_id: int
    status: str
    recruiter_notes: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime
    feedback_entries: List[ClientFeedbackResponse] = []
    interviews: List[InterviewResponse] = []
    candidate_details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

