from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ConsentRecordRequest(BaseModel):
    consent_given: bool = True
    purpose_of_processing: str = "Recruitment evaluation, scorecard matching and client submission"
    valid_until_months: int = 12
    notes: Optional[str] = None


class ConsentResponse(BaseModel):
    id: int
    candidate_id: int
    consent_given: bool
    consent_timestamp: datetime
    purpose_of_processing: str
    valid_until: Optional[datetime]
    ip_address: str
    notes: Optional[str]

    class Config:
        from_attributes = True


class DeletionRequestCreate(BaseModel):
    reason: Optional[str] = "Candidate requested data deletion under DPDP Act principles"


class DeletionRequestResponse(BaseModel):
    id: int
    candidate_id: int
    requested_at: datetime
    status: str
    reason: Optional[str]
    completed_at: Optional[datetime]
    executed_by_id: Optional[int]

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_email: Optional[str]
    user_role: Optional[str]
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    ip_address: str
    created_at: datetime

    class Config:
        from_attributes = True

