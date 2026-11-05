import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.base import Base


class DeletionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"


class CandidateConsent(Base):
    """
    Candidate privacy & consent tracking conforming with
    India's Digital Personal Data Protection (DPDP) Act, 2023 principles.
    """
    __tablename__ = "candidate_consents"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    
    consent_given = Column(Boolean, default=True, nullable=False)
    consent_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    purpose_of_processing = Column(String(255), default="Recruitment evaluation, scorecard matching and client submission", nullable=False)
    valid_until = Column(DateTime, nullable=True)
    ip_address = Column(String(50), default="127.0.0.1")
    notes = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="consent_records")


class CandidateDeletionRequest(Base):
    """
    Candidate Right to Erasure / Deletion workflow under DPDP Act principles.
    """
    __tablename__ = "candidate_deletion_requests"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(DeletionStatus), default=DeletionStatus.PENDING, nullable=False)
    reason = Column(Text, nullable=True)
    
    completed_at = Column(DateTime, nullable=True)
    executed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    candidate = relationship("Candidate", back_populates="deletion_requests")

