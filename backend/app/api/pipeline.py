from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.rbac import get_current_user, require_recruiter
from app.database.session import get_db
from app.models.user import User
from app.models.requisition import Requisition
from app.models.candidate import Candidate
from app.models.score import CandidateScore
from app.models.pipeline import CandidatePipelineHistory, VALID_STAGES
from app.models.client import ClientSubmission
from app.models.audit import AuditLog
from app.schemas.pipeline import PipelineTransitionRequest, PipelineHistoryResponse

router = APIRouter(tags=["Recruitment Pipeline"])


@router.get("/api/requisitions/{id}/pipeline")
def get_requisition_pipeline(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requisition).filter(Requisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")

    if current_user.role.value == "client_hiring_manager":
        if req.client_org_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

    candidates = db.query(Candidate).filter(Candidate.is_active == True).all()

    # Build Kanban column structure for each valid stage
    stage_columns = {stage: [] for stage in VALID_STAGES}

    for cand in candidates:
        score = db.query(CandidateScore).filter(
            CandidateScore.candidate_id == cand.id,
            CandidateScore.requisition_id == id
        ).order_by(desc(CandidateScore.created_at)).first()

        current_stage = cand.current_stage if cand.current_stage in stage_columns else "Parsed"
        
        # Determine candidate card display
        cand_card = {
            "id": cand.id,
            "candidate_code": cand.candidate_code,
            "name": f"{cand.first_name} {cand.last_name}" if current_user.role.value != "client_hiring_manager" else f"{cand.first_name[0]}**** {cand.last_name[0]}****",
            "current_role": cand.current_role,
            "total_experience_years": cand.total_experience_years,
            "notice_period_days": cand.notice_period_days,
            "score": score.total_score if score else 0.0,
            "grade": score.match_grade if score else "Unscored",
            "skills": cand.skills[:4] if cand.skills else []
        }
        stage_columns[current_stage].append(cand_card)

    return {
        "requisition_id": id,
        "requisition_title": req.title,
        "stages": [
            {
                "stage_name": stage,
                "count": len(cands),
                "candidates": cands
            } for stage, cands in stage_columns.items()
        ]
    }


@router.patch("/api/candidates/{id}/pipeline")
def update_candidate_pipeline_stage(
    id: int,
    trans_req: PipelineTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    target_stage = trans_req.to_stage.strip()
    if target_stage not in VALID_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target pipeline stage '{target_stage}'. Valid stages: {VALID_STAGES}"
        )

    # Permission checks: Client hiring manager can only perform review transitions
    if current_user.role.value == "client_hiring_manager":
        allowed_client_stages = ["Client Approved", "Interview Scheduled", "Rejected"]
        if target_stage not in allowed_client_stages:
            raise HTTPException(
                status_code=403,
                detail=f"Client Hiring Managers can only transition to: {allowed_client_stages}"
            )

    old_stage = candidate.current_stage
    candidate.current_stage = target_stage

    # Record history
    hist = CandidatePipelineHistory(
        candidate_id=candidate.id,
        requisition_id=1,  # Default active requisition
        from_stage=old_stage,
        to_stage=target_stage,
        changed_by_id=current_user.id,
        notes=trans_req.notes or f"Transitioned from {old_stage} to {target_stage}"
    )
    db.add(hist)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="PIPELINE_STAGE_TRANSITION",
        resource_type="candidate",
        resource_id=candidate.candidate_code,
        details={"from_stage": old_stage, "to_stage": target_stage, "notes": trans_req.notes}
    )
    db.add(audit)
    db.commit()

    return {
        "candidate_id": candidate.id,
        "from_stage": old_stage,
        "to_stage": target_stage,
        "message": f"Candidate successfully moved to {target_stage}"
    }


@router.get("/api/candidates/{id}/pipeline-history", response_model=List[PipelineHistoryResponse])
def get_candidate_pipeline_history(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history = db.query(CandidatePipelineHistory).filter(
        CandidatePipelineHistory.candidate_id == id
    ).order_by(desc(CandidatePipelineHistory.created_at)).all()
    return history

