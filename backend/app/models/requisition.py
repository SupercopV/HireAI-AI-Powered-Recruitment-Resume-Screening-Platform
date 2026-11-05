import enum
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Enum, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base


class RequisitionStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class Requisition(Base):
    __tablename__ = "requisitions"

    id = Column(Integer, primary_key=True, index=True)
    requisition_code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(100), default="Engineering")
    location = Column(String(100), default="Noida")
    experience_min = Column(Float, default=0.0)
    experience_max = Column(Float, default=10.0)
    ctc_min_lpa = Column(Float, default=0.0)
    ctc_max_lpa = Column(Float, default=0.0)
    employment_type = Column(String(50), default="Full-Time")  # Full-Time, Contract, Hybrid
    max_notice_period_days = Column(Integer, default=60)
    description = Column(Text, nullable=False)
    status = Column(Enum(RequisitionStatus), default=RequisitionStatus.ACTIVE, nullable=False)
    
    client_org_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scorecards = relationship("JobScorecard", back_populates="requisition", cascade="all, delete-orphan", order_by="desc(JobScorecard.version)")
    resumes = relationship("Resume", back_populates="requisition")
    upload_batches = relationship("ResumeUploadBatch", back_populates="requisition")
    submissions = relationship("ClientSubmission", back_populates="requisition")
    candidate_scores = relationship("CandidateScore", back_populates="requisition")
    pipeline_entries = relationship("CandidatePipelineHistory", back_populates="requisition")


class JobScorecard(Base):
    __tablename__ = "job_scorecards"

    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    # AI-extracted & recruiter-editable fields (Stored as structured JSON)
    must_have_skills = Column(JSON, default=list)  # e.g. ["Java", "Spring Boot", "Microservices"]
    good_to_have_skills = Column(JSON, default=list)  # e.g. ["Docker", "Kubernetes", "Kafka"]
    min_experience = Column(Float, default=0.0)
    max_experience = Column(Float, default=10.0)
    location = Column(String(100), default="Noida")
    max_notice_period = Column(Integer, default=60)
    ctc_info = Column(String(255), default="")

    # Configurable weights (Total: 100)
    # Default: required_skills: 40, exp_match: 25, relevant_exp: 15, good_to_have: 10, notice_period: 10
    weights = Column(JSON, default=lambda: {
        "required_skills": 40,
        "experience_match": 25,
        "relevant_experience": 15,
        "good_to_have_skills": 10,
        "notice_period": 10
    })

    is_approved = Column(Boolean, default=False)
    raw_ai_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requisition = relationship("Requisition", back_populates="scorecards")
    scores = relationship("CandidateScore", back_populates="scorecard")

