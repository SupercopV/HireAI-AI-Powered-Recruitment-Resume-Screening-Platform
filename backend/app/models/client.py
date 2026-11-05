import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from app.database.base import Base


class SubmissionStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    INTERVIEW_REQUESTED = "interview_requested"


class ClientSubmission(Base):
    __tablename__ = "client_submissions"

    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    client_org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    submitted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING_REVIEW, nullable=False)
    recruiter_notes = Column(Text, nullable=True)
    
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    requisition = relationship("Requisition", back_populates="submissions")
    candidate = relationship("Candidate", back_populates="submissions")
    client_org = relationship("Organization", back_populates="submissions")
    feedback_entries = relationship("ClientFeedback", back_populates="submission", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="submission", cascade="all, delete-orphan")


class ClientFeedback(Base):
    __tablename__ = "client_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("client_submissions.id", ondelete="CASCADE"), nullable=False)
    client_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    action = Column(String(50), nullable=False)  # "shortlist", "reject", "request_interview"
    rejection_reason = Column(String(255), nullable=True)  # Mandatory when rejecting
    feedback_text = Column(Text, nullable=True)
    proposed_interview_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    submission = relationship("ClientSubmission", back_populates="feedback_entries")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("client_submissions.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True)
    
    round_name = Column(String(100), default="Technical Round 1")
    scheduled_time = Column(DateTime, nullable=False)
    interviewer_name = Column(String(255), default="Client Technical Lead")
    meeting_link = Column(String(500), default="")
    status = Column(String(50), default="scheduled")  # scheduled, completed, cancelled, no-show
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    submission = relationship("ClientSubmission", back_populates="interviews")

