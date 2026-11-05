import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Enum, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base


class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ParsingStatus(str, enum.Enum):
    PENDING = "pending"
    PARSED = "parsed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    candidate_code = Column(String(50), unique=True, index=True, nullable=False)  # e.g. CND-91022
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(50), index=True, nullable=True)
    
    current_role = Column(String(255), nullable=True)
    total_experience_years = Column(Float, default=0.0)
    relevant_experience_years = Column(Float, default=0.0)
    skills = Column(JSON, default=list)  # List of normalized skill strings
    notice_period_days = Column(Integer, default=30)
    current_location = Column(String(100), default="")
    education = Column(String(255), default="")
    summary = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)  # Extracted text from resume for exact evidence matching

    # Current pipeline stage for default/latest requisition
    current_stage = Column(String(50), default="Parsed")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    scores = relationship("CandidateScore", back_populates="candidate", cascade="all, delete-orphan")
    submissions = relationship("ClientSubmission", back_populates="candidate", cascade="all, delete-orphan")
    pipeline_history = relationship("CandidatePipelineHistory", back_populates="candidate", cascade="all, delete-orphan")
    consent_records = relationship("CandidateConsent", back_populates="candidate", cascade="all, delete-orphan")
    deletion_requests = relationship("CandidateDeletionRequest", back_populates="candidate", cascade="all, delete-orphan")


class ResumeUploadBatch(Base):
    __tablename__ = "resume_upload_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_code = Column(String(50), unique=True, index=True, nullable=False)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False)
    total_files = Column(Integer, default=0)
    parsed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    status = Column(Enum(BatchStatus), default=BatchStatus.COMPLETED)
    created_at = Column(DateTime, default=datetime.utcnow)

    requisition = relationship("Requisition", back_populates="upload_batches")
    resumes = relationship("Resume", back_populates="batch", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="SET NULL"), nullable=True)
    batch_id = Column(Integer, ForeignKey("resume_upload_batches.id", ondelete="SET NULL"), nullable=True)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), index=True, nullable=False)  # SHA-256 for exact duplicate file check
    file_type = Column(String(20), default="pdf")  # pdf or docx
    file_size_bytes = Column(Integer, default=0)
    
    parsed_text = Column(Text, nullable=True)
    parsing_status = Column(Enum(ParsingStatus), default=ParsingStatus.PENDING)
    parsing_error = Column(Text, nullable=True)
    ocr_applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="resumes")
    requisition = relationship("Requisition", back_populates="resumes")
    batch = relationship("ResumeUploadBatch", back_populates="resumes")

