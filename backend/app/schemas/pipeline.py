from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PipelineTransitionRequest(BaseModel):
    to_stage: str = Field(..., description="Target pipeline stage")
    notes: Optional[str] = None


class PipelineHistoryResponse(BaseModel):
    id: int
    candidate_id: int
    requisition_id: int
    from_stage: Optional[str]
    to_stage: str
    changed_by_id: Optional[int]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PipelineStageOverview(BaseModel):
    stage_name: str
    count: int
    candidates: List[dict] = []

