import random
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.rbac import get_current_user, require_recruiter
from app.database.session import get_db
from app.models.user import User
from app.models.requisition import Requisition, JobScorecard, RequisitionStatus
from app.models.candidate import Candidate
from app.models.score import CandidateScore
from app.models.audit import AuditLog
from app.schemas.requisition import RequisitionCreate, RequisitionUpdate, RequisitionResponse

router = APIRouter(prefix="/api/requisitions", tags=["Requisitions"])


@router.get("", response_model=List[RequisitionResponse])
def get_requisitions(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Requisition)
    if status:
        query = query.filter(Requisition.status == status)
    
    # If client hiring manager, filter requisitions submitted or assigned to their org
    if current_user.role.value == "client_hiring_manager":
        query = query.filter(Requisition.client_org_id == current_user.organization_id)

    requisitions = query.order_by(Requisition.created_at.desc()).all()

    # Populate candidates_count
    for req in requisitions:
        req.candidates_count = db.query(CandidateScore).filter(CandidateScore.requisition_id == req.id).count()

    return requisitions


@router.post("", response_model=RequisitionResponse)
def create_requisition(
    req_data: RequisitionCreate,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    code = f"REQ-{random.randint(10000, 99999)}"
    
    new_req = Requisition(
        requisition_code=code,
        title=req_data.title,
        department=req_data.department,
        location=req_data.location,
        experience_min=req_data.experience_min,
        experience_max=req_data.experience_max,
        ctc_min_lpa=req_data.ctc_min_lpa,
        ctc_max_lpa=req_data.ctc_max_lpa,
        employment_type=req_data.employment_type,
        max_notice_period_days=req_data.max_notice_period_days,
        description=req_data.description,
        client_org_id=req_data.client_org_id,
        created_by_id=current_user.id,
        status=RequisitionStatus.ACTIVE
    )
    db.add(new_req)
    db.flush()

    # Auto-initialize version 1 scorecard
    scorecard = JobScorecard(
        requisition_id=new_req.id,
        version=1,
        must_have_skills=["Java", "Spring Boot", "Microservices"] if "java" in req_data.title.lower() else ["Technical Leadership", "System Design"],
        good_to_have_skills=["Docker", "Kubernetes", "Kafka"],
        min_experience=req_data.experience_min,
        max_experience=req_data.experience_max,
        location=req_data.location,
        max_notice_period=req_data.max_notice_period_days,
        ctc_info=f"{req_data.ctc_min_lpa} - {req_data.ctc_max_lpa} LPA",
        is_approved=False
    )
    db.add(scorecard)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="CREATE_REQUISITION",
        resource_type="requisition",
        resource_id=code,
        details={"title": req_data.title, "code": code}
    )
    db.add(audit)
    db.commit()
    db.refresh(new_req)
    return new_req


@router.get("/{id}", response_model=RequisitionResponse)
def get_requisition(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requisition).filter(Requisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")

    # Client data isolation check
    if current_user.role.value == "client_hiring_manager":
        if req.client_org_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to this requisition")

    req.candidates_count = db.query(CandidateScore).filter(CandidateScore.requisition_id == req.id).count()
    return req


@router.put("/{id}", response_model=RequisitionResponse)
def update_requisition(
    id: int,
    req_update: RequisitionUpdate,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    req = db.query(Requisition).filter(Requisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")

    update_data = req_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if field == "status" and val:
            setattr(req, field, RequisitionStatus(val))
        else:
            setattr(req, field, val)

    db.commit()
    db.refresh(req)
    return req

