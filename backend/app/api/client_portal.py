from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.rbac import get_current_user, require_client, require_recruiter
from app.database.session import get_db
from app.models.user import User, Organization
from app.models.requisition import Requisition
from app.models.candidate import Candidate
from app.models.score import CandidateScore
from app.models.client import ClientSubmission, ClientFeedback, Interview, SubmissionStatus
from app.models.pipeline import CandidatePipelineHistory
from app.models.audit import AuditLog
from app.schemas.client import (
    SubmissionCreate,
    ClientSubmissionResponse,
    ClientShortlistRequest,
    ClientRejectRequest,
    ClientInterviewRequest,
    InterviewResponse
)
from app.schemas.candidate import CandidateMaskedResponse

router = APIRouter(prefix="/api/client", tags=["Client Portal"])


def mask_string(val: Optional[str], show_start: int = 1, show_end: int = 1) -> str:
    if not val:
        return "Protected"
    if len(val) <= show_start + show_end:
        return "*" * len(val)
    return val[:show_start] + ("*" * (len(val) - show_start - show_end)) + val[-show_end:]


def mask_email(email: Optional[str]) -> str:
    if not email or "@" not in email:
        return "c***@***.com"
    parts = email.split("@")
    user_part = parts[0]
    domain_part = parts[1]
    masked_user = user_part[0] + "***" if len(user_part) > 1 else "***"
    return f"{masked_user}@{domain_part}"


def mask_phone(phone: Optional[str]) -> str:
    if not phone:
        return "+91 ******0000"
    clean = phone.replace(" ", "").replace("-", "")
    if len(clean) >= 10:
        return clean[:4] + "******" + clean[-2:]
    return "+91 ******" + clean[-2:]


@router.get("/submissions", response_model=List[CandidateMaskedResponse])
def get_client_submissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get candidates submitted to client organization.
    Strictly isolated: Client users can ONLY view candidates submitted to their assigned organization.
    Candidate personal contact information is masked.
    """
    query = db.query(ClientSubmission)
    
    if current_user.role.value == "client_hiring_manager":
        if not current_user.organization_id:
            return []
        query = query.filter(ClientSubmission.client_org_id == current_user.organization_id)

    submissions = query.order_by(desc(ClientSubmission.created_at)).all()
    results = []

    for sub in submissions:
        cand = sub.candidate
        if not cand:
            continue

        score = db.query(CandidateScore).filter(
            CandidateScore.candidate_id == cand.id,
            CandidateScore.requisition_id == sub.requisition_id
        ).order_by(desc(CandidateScore.created_at)).first()

        masked_item = CandidateMaskedResponse(
            id=cand.id,
            candidate_code=cand.candidate_code,
            masked_name=f"{cand.first_name[0]}**** {cand.last_name[0]}****",
            masked_email=mask_email(cand.email),
            masked_phone=mask_phone(cand.phone),
            current_role=cand.current_role,
            total_experience_years=cand.total_experience_years,
            skills=cand.skills or [],
            notice_period_days=cand.notice_period_days,
            education=cand.education,
            summary=cand.summary,
            current_stage=cand.current_stage,
            created_at=sub.created_at,
            submission_id=sub.id,
            submission_status=sub.status.value,
            recruiter_notes=sub.recruiter_notes,
            latest_score={
                "total_score": score.total_score,
                "match_grade": score.match_grade,
                "matching_skills": score.matching_skills,
                "missing_skills": score.missing_skills,
                "ai_reasoning": score.ai_reasoning
            } if score else None
        )
        results.append(masked_item)

    return results


@router.post("/submissions", response_model=ClientSubmissionResponse)
def submit_candidate_to_client(
    sub_data: SubmissionCreate,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    """
    Recruiter submits a candidate to a client organization with notes.
    """
    existing = db.query(ClientSubmission).filter(
        ClientSubmission.requisition_id == sub_data.requisition_id,
        ClientSubmission.candidate_id == sub_data.candidate_id,
        ClientSubmission.client_org_id == sub_data.client_org_id
    ).first()

    if existing:
        existing.recruiter_notes = sub_data.recruiter_notes
        existing.status = SubmissionStatus.PENDING_REVIEW
        db.commit()
        db.refresh(existing)
        return existing

    submission = ClientSubmission(
        requisition_id=sub_data.requisition_id,
        candidate_id=sub_data.candidate_id,
        client_org_id=sub_data.client_org_id,
        submitted_by_id=current_user.id,
        status=SubmissionStatus.PENDING_REVIEW,
        recruiter_notes=sub_data.recruiter_notes
    )
    db.add(submission)

    # Transition pipeline stage
    cand = db.query(Candidate).filter(Candidate.id == sub_data.candidate_id).first()
    if cand:
        old_stage = cand.current_stage
        cand.current_stage = "Submitted to Client"
        hist = CandidatePipelineHistory(
            candidate_id=cand.id,
            requisition_id=sub_data.requisition_id,
            from_stage=old_stage,
            to_stage="Submitted to Client",
            changed_by_id=current_user.id,
            notes=f"Submitted to client organization with notes: {sub_data.recruiter_notes or 'None'}"
        )
        db.add(hist)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="SUBMIT_TO_CLIENT",
        resource_type="submission",
        resource_id=f"cand-{sub_data.candidate_id}",
        details={"client_org_id": sub_data.client_org_id}
    )
    db.add(audit)
    db.commit()
    db.refresh(submission)
    return submission


@router.post("/submissions/{id}/shortlist")
def shortlist_submission(
    id: int,
    req: ClientShortlistRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = db.query(ClientSubmission).filter(ClientSubmission.id == id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.role.value == "client_hiring_manager":
        if sub.client_org_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

    sub.status = SubmissionStatus.SHORTLISTED
    sub.reviewed_by_id = current_user.id
    sub.reviewed_at = datetime.utcnow()

    feedback = ClientFeedback(
        submission_id=sub.id,
        client_user_id=current_user.id,
        action="shortlist",
        feedback_text=req.feedback_text
    )
    db.add(feedback)

    # Update candidate pipeline stage
    if sub.candidate:
        old_stage = sub.candidate.current_stage
        sub.candidate.current_stage = "Client Approved"
        hist = CandidatePipelineHistory(
            candidate_id=sub.candidate.id,
            requisition_id=sub.requisition_id,
            from_stage=old_stage,
            to_stage="Client Approved",
            changed_by_id=current_user.id,
            notes=f"Approved and shortlisted by Client Hiring Manager: {req.feedback_text}"
        )
        db.add(hist)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="CLIENT_SHORTLIST_CANDIDATE",
        resource_type="submission",
        resource_id=str(sub.id),
        details={"feedback": req.feedback_text}
    )
    db.add(audit)
    db.commit()
    return {"message": "Candidate shortlisted successfully by Client", "status": "shortlisted"}


@router.post("/submissions/{id}/reject")
def reject_submission(
    id: int,
    req: ClientRejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = db.query(ClientSubmission).filter(ClientSubmission.id == id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.role.value == "client_hiring_manager":
        if sub.client_org_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

    if not req.rejection_reason or len(req.rejection_reason.strip()) < 3:
        raise HTTPException(status_code=400, detail="Mandatory rejection reason must be provided")

    sub.status = SubmissionStatus.REJECTED
    sub.reviewed_by_id = current_user.id
    sub.reviewed_at = datetime.utcnow()

    feedback = ClientFeedback(
        submission_id=sub.id,
        client_user_id=current_user.id,
        action="reject",
        rejection_reason=req.rejection_reason,
        feedback_text=req.feedback_text
    )
    db.add(feedback)

    # Update candidate pipeline stage
    if sub.candidate:
        old_stage = sub.candidate.current_stage
        sub.candidate.current_stage = "Rejected"
        hist = CandidatePipelineHistory(
            candidate_id=sub.candidate.id,
            requisition_id=sub.requisition_id,
            from_stage=old_stage,
            to_stage="Rejected",
            changed_by_id=current_user.id,
            notes=f"Rejected by client. Mandatory reason: {req.rejection_reason}"
        )
        db.add(hist)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="CLIENT_REJECT_CANDIDATE",
        resource_type="submission",
        resource_id=str(sub.id),
        details={"rejection_reason": req.rejection_reason}
    )
    db.add(audit)
    db.commit()
    return {"message": "Candidate rejected with reason recorded", "status": "rejected"}


@router.post("/submissions/{id}/interview")
def propose_interview(
    id: int,
    req: ClientInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = db.query(ClientSubmission).filter(ClientSubmission.id == id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.role.value == "client_hiring_manager":
        if sub.client_org_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

    sub.status = SubmissionStatus.INTERVIEW_REQUESTED
    sub.reviewed_by_id = current_user.id
    sub.reviewed_at = datetime.utcnow()

    feedback = ClientFeedback(
        submission_id=sub.id,
        client_user_id=current_user.id,
        action="request_interview",
        feedback_text=req.feedback_text,
        proposed_interview_time=req.proposed_interview_time
    )
    db.add(feedback)

    interview = Interview(
        submission_id=sub.id,
        candidate_id=sub.candidate_id,
        round_name=req.round_name or "Technical Round 1",
        scheduled_time=req.proposed_interview_time,
        interviewer_name=req.interviewer_name or "Client Technical Lead",
        meeting_link=req.meeting_link or "https://meet.google.com/hireai-interview",
        status="scheduled"
    )
    db.add(interview)

    # Update candidate pipeline stage
    if sub.candidate:
        old_stage = sub.candidate.current_stage
        sub.candidate.current_stage = "Interview Scheduled"
        hist = CandidatePipelineHistory(
            candidate_id=sub.candidate.id,
            requisition_id=sub.requisition_id,
            from_stage=old_stage,
            to_stage="Interview Scheduled",
            changed_by_id=current_user.id,
            notes=f"Interview proposed for {req.proposed_interview_time.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        db.add(hist)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="PROPOSE_INTERVIEW",
        resource_type="interview",
        resource_id=str(sub.id),
        details={"scheduled_time": req.proposed_interview_time.isoformat()}
    )
    db.add(audit)
    db.commit()
    return {"message": "Interview requested and scheduled", "interview_time": req.proposed_interview_time}

