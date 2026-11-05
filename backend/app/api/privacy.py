import os
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.rbac import get_current_user, require_recruiter
from app.database.session import get_db
from app.models.user import User
from app.models.candidate import Candidate, Resume
from app.models.privacy import CandidateConsent, CandidateDeletionRequest, DeletionStatus
from app.models.audit import AuditLog
from app.schemas.privacy import ConsentRecordRequest, ConsentResponse, DeletionRequestCreate, DeletionRequestResponse

router = APIRouter(prefix="/api/candidates/{id}", tags=["Candidate Privacy & DPDP Compliance"])


@router.post("/consent", response_model=ConsentResponse)
def record_candidate_consent(
    id: int,
    req: ConsentRecordRequest,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    valid_until = datetime.utcnow() + timedelta(days=req.valid_until_months * 30)
    consent = CandidateConsent(
        candidate_id=candidate.id,
        consent_given=req.consent_given,
        consent_timestamp=datetime.utcnow(),
        purpose_of_processing=req.purpose_of_processing,
        valid_until=valid_until,
        ip_address="127.0.0.1",
        notes=req.notes
    )
    db.add(consent)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="RECORD_CANDIDATE_CONSENT",
        resource_type="privacy",
        resource_id=candidate.candidate_code,
        details={"purpose": req.purpose_of_processing, "valid_until": valid_until.isoformat()}
    )
    db.add(audit)
    db.commit()
    db.refresh(consent)
    return consent


@router.post("/deletion-request", response_model=DeletionRequestResponse)
def create_deletion_request(
    id: int,
    req: DeletionRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    del_request = CandidateDeletionRequest(
        candidate_id=candidate.id,
        reason=req.reason,
        status=DeletionStatus.COMPLETED,  # Execute workflow
        completed_at=datetime.utcnow(),
        executed_by_id=current_user.id
    )
    db.add(del_request)

    # DPDP Act Workflow: Anonymize personal identifier fields
    candidate.first_name = "Deleted"
    candidate.last_name = "User"
    candidate.email = f"deleted_{candidate.id}@anonymized.local"
    candidate.phone = "+91 0000000000"
    candidate.raw_text = "[Personal resume data erased under DPDP right-to-erasure request]"
    candidate.summary = "[Profile data deleted]"
    candidate.is_active = False

    # Remove resume files from storage if present
    resumes = db.query(Resume).filter(Resume.candidate_id == id).all()
    for res in resumes:
        if res.file_path and os.path.exists(res.file_path):
            try:
                os.remove(res.file_path)
            except Exception:
                pass
        res.parsed_text = "[Erased]"
        res.file_path = ""

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="EXECUTE_DPDP_DELETION",
        resource_type="privacy",
        resource_id=candidate.candidate_code,
        details={"reason": req.reason, "status": "COMPLETED"}
    )
    db.add(audit)
    db.commit()
    db.refresh(del_request)
    return del_request


@router.get("/privacy")
def get_candidate_privacy_info(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    consents = db.query(CandidateConsent).filter(CandidateConsent.candidate_id == id).all()
    deletions = db.query(CandidateDeletionRequest).filter(CandidateDeletionRequest.candidate_id == id).all()

    return {
        "candidate_id": candidate.id,
        "candidate_code": candidate.candidate_code,
        "is_active": candidate.is_active,
        "consents": [
            {
                "id": c.id,
                "consent_given": c.consent_given,
                "timestamp": c.consent_timestamp.isoformat(),
                "purpose": c.purpose_of_processing,
                "valid_until": c.valid_until.isoformat() if c.valid_until else None
            } for c in consents
        ],
        "deletion_requests": [
            {
                "id": d.id,
                "requested_at": d.requested_at.isoformat(),
                "status": d.status.value,
                "reason": d.reason,
                "completed_at": d.completed_at.isoformat() if d.completed_at else None
            } for d in deletions
        ]
    }

