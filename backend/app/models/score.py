from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base


class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False)
    scorecard_id = Column(Integer, ForeignKey("job_scorecards.id", ondelete="CASCADE"), nullable=False)

    total_score = Column(Float, default=0.0, nullable=False, index=True)
    max_possible_score = Column(Float, default=100.0)

    # Breakdown based on configured weights
    required_skills_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    relevant_experience_score = Column(Float, default=0.0)
    good_to_have_score = Column(Float, default=0.0)
    notice_period_score = Column(Float, default=0.0)

    matching_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    match_grade = Column(String(20), default="Moderate")  # High Match, Moderate, Low Match

    ai_reasoning = Column(Text, nullable=True)
    is_demo_score = Column(Boolean, default=False)  # Clearly labels if deterministic fallback / demo mode
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="scores")
    requisition = relationship("Requisition", back_populates="candidate_scores")
    scorecard = relationship("JobScorecard", back_populates="scores")
    evidence_items = relationship("ScoreEvidence", back_populates="candidate_score", cascade="all, delete-orphan")


class ScoreEvidence(Base):
    __tablename__ = "score_evidences"

    id = Column(Integer, primary_key=True, index=True)
    candidate_score_id = Column(Integer, ForeignKey("candidate_scores.id", ondelete="CASCADE"), nullable=False)

    criterion_name = Column(String(100), nullable=False)  # e.g. "Required Skills", "Experience Match"
    max_score = Column(Float, default=0.0)
    awarded_score = Column(Float, default=0.0)
    evidence_quote = Column(Text, nullable=False)  # Exact quote from CV or "Evidence not found"
    explanation = Column(Text, nullable=False)
    missing_info = Column(Text, nullable=True)

    candidate_score = relationship("CandidateScore", back_populates="evidence_items")

