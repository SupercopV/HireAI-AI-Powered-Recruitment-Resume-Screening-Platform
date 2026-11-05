from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

# 11 Standard recruitment pipeline stages:
# Sourced, Parsed, Screened, Shortlisted, Submitted to Client, Client Approved,
# Interview Scheduled, Interviewed, Offered, Joined, Rejected

VALID_STAGES = [
    "Sourced",
    "Parsed",
    "Screened",
    "Shortlisted",
    "Submitted to Client",
    "Client Approved",
    "Interview Scheduled",
    "Interviewed",
    "Offered",
    "Joined",
    "Rejected"
]


class CandidatePipelineHistory(Base):
    __tablename__ = "candidate_pipeline_history"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False)
    from_stage = Column(String(50), nullable=True)
    to_stage = Column(String(50), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="pipeline_history")
    requisition = relationship("Requisition", back_populates="pipeline_entries")

