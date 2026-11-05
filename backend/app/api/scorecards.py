from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.rbac import require_recruiter, get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.requisition import Requisition, JobScorecard
from app.models.audit import AuditLog
from app.schemas.requisition import JDAnalysisRequest, JDAnalysisResponse, ScorecardUpdate, ScorecardResponse
from app.services.groq_service import GroqAIService

router = APIRouter(prefix="/api/requisitions/{id}", tags=["Scorecards"])


@router.get("/scorecard", response_model=ScorecardResponse)
def get_scorecard(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requisition).filter(Requisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")

    scorecard = db.query(JobScorecard).filter(JobScorecard.requisition_id == id).order_by(JobScorecard.version.desc()).first()
    if not scorecard:
        raise HTTPException(status_code=404, detail="Scorecard not found for this requisition")
    return scorecard


@router.post("/analyze-jd", response_model=JDAnalysisResponse)
def analyze_jd(
    id: int,
    analysis_req: JDAnalysisRequest,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    req = db.query(Requisition).filter(Requisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")

    title = analysis_req.job_title or req.title
    extracted_data, is_demo = GroqAIService.analyze_job_description(
        analysis_req.job_description_text,
        job_title=title
    )

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="ANALYZE_JOB_DESCRIPTION",
        resource_type="requisition",
        resource_id=req.requisition_code,
        details={"is_demo_mode": is_demo, "skills_extracted": len(extracted_data.must_have_skills)}
    )
    db.add(audit)
    db.commit()

    return extracted_data


@router.put("/scorecard", response_model=ScorecardResponse)
def update_or_approve_scorecard(
    id: int,
    card_update: ScorecardUpdate,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    req = db.query(Requisition).filter(Requisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")

    existing_card = db.query(JobScorecard).filter(JobScorecard.requisition_id == id).order_by(JobScorecard.version.desc()).first()
    
    if existing_card:
        # Update existing or increment version if previously approved
        if existing_card.is_approved:
            new_card = JobScorecard(
                requisition_id=id,
                version=existing_card.version + 1,
                must_have_skills=card_update.must_have_skills,
                good_to_have_skills=card_update.good_to_have_skills,
                min_experience=card_update.min_experience,
                max_experience=card_update.max_experience,
                location=card_update.location,
                max_notice_period=card_update.max_notice_period,
                ctc_info=card_update.ctc_info,
                weights=card_update.weights,
                is_approved=card_update.is_approved
            )
            db.add(new_card)
            db.commit()
            db.refresh(new_card)
            return new_card
        else:
            existing_card.must_have_skills = card_update.must_have_skills
            existing_card.good_to_have_skills = card_update.good_to_have_skills
            existing_card.min_experience = card_update.min_experience
            existing_card.max_experience = card_update.max_experience
            existing_card.location = card_update.location
            existing_card.max_notice_period = card_update.max_notice_period
            existing_card.ctc_info = card_update.ctc_info
            existing_card.weights = card_update.weights
            existing_card.is_approved = card_update.is_approved
            db.commit()
            db.refresh(existing_card)
            return existing_card
    else:
        new_card = JobScorecard(
            requisition_id=id,
            version=1,
            must_have_skills=card_update.must_have_skills,
            good_to_have_skills=card_update.good_to_have_skills,
            min_experience=card_update.min_experience,
            max_experience=card_update.max_experience,
            location=card_update.location,
            max_notice_period=card_update.max_notice_period,
            ctc_info=card_update.ctc_info,
            weights=card_update.weights,
            is_approved=card_update.is_approved
        )
        db.add(new_card)
        db.commit()
        db.refresh(new_card)
        return new_card

