from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base


class AuditLog(Base):
    """
    Immutable audit logging for security, compliance,
    and DPDP tracking (who viewed candidate profiles and when).
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)
    
    action = Column(String(100), nullable=False)  # e.g. "VIEW_CANDIDATE_PROFILE", "SHORTLIST_CANDIDATE", "GENERATE_SCORE"
    resource_type = Column(String(50), nullable=False)  # "candidate", "submission", "scorecard", "resume"
    resource_id = Column(String(100), nullable=False)
    
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), default="127.0.0.1")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")

