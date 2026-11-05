from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.rbac import require_recruiter, get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.requisition import Requisition, JobScorecard
from app.models.candidate import Candidate
from app.models.score import CandidateScore, ScoreEvidence
from app.models.audit import AuditLog
from app.schemas.score import CandidateScoreResponse, ScoreCalculationRequest
from app.services.scoring_engine import DeterministicScoringEngine
from app.services.groq_service import GroqAIService

router = APIRouter(tags=["AI Scoring"])


@router.post("/api/candidates/{id}/score", response_model=CandidateScoreResponse)
def score_candidate(
    id: int,
    calc_req: ScoreCalculationRequest,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    requisition = db.query(Requisition).filter(Requisition.id == calc_req.requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")

    scorecard = db.query(JobScorecard).filter(
        JobScorecard.requisition_id == calc_req.requisition_id
    ).order_by(desc(JobScorecard.version)).first()
    if not scorecard:
        raise HTTPException(status_code=400, detail="Scorecard has not been configured for this requisition")

    # Deterministic scoring execution
    score_data = DeterministicScoringEngine.calculate_candidate_score(
        candidate, scorecard, override_weights=calc_req.override_weights
    )

    is_demo = not GroqAIService.is_groq_available()

    # Create new CandidateScore record
    new_score = CandidateScore(
        candidate_id=candidate.id,
        requisition_id=requisition.id,
        scorecard_id=scorecard.id,
        total_score=score_data["total_score"],
        max_possible_score=score_data["max_possible_score"],
        required_skills_score=score_data["required_skills_score"],
        experience_score=score_data["experience_score"],
        relevant_experience_score=score_data["relevant_experience_score"],
        good_to_have_score=score_data["good_to_have_score"],
        notice_period_score=score_data["notice_period_score"],
        matching_skills=score_data["matching_skills"],
        missing_skills=score_data["missing_skills"],
        match_grade=score_data["match_grade"],
        ai_reasoning=score_data["ai_reasoning"],
        is_demo_score=is_demo
    )
    db.add(new_score)
    db.flush()

    # Create exact evidence items
    for ev in score_data["evidence_items"]:
        ev_model = ScoreEvidence(
            candidate_score_id=new_score.id,
            criterion_name=ev["criterion_name"],
            max_score=ev["max_score"],
            awarded_score=ev["awarded_score"],
            evidence_quote=ev["evidence_quote"],
            explanation=ev["explanation"],
            missing_info=ev.get("missing_info")
        )
        db.add(ev_model)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="CALCULATE_CANDIDATE_SCORE",
        resource_type="score",
        resource_id=str(new_score.id),
        details={
            "candidate_code": candidate.candidate_code,
            "total_score": new_score.total_score,
            "match_grade": new_score.match_grade
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(new_score)
    return new_score


@router.get("/api/candidates/{id}/score", response_model=CandidateScoreResponse)
def get_candidate_score(
    id: int,
    requisition_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(CandidateScore).filter(CandidateScore.candidate_id == id)
    if requisition_id:
        query = query.filter(CandidateScore.requisition_id == requisition_id)
    
    score = query.order_by(desc(CandidateScore.created_at)).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score record not found for candidate")
    return score


@router.post("/api/requisitions/{id}/score-all")
def score_all_candidates(
    id: int,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    req = db.query(Requisition).filter(Requisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")

    scorecard = db.query(JobScorecard).filter(JobScorecard.requisition_id == id).order_by(desc(JobScorecard.version)).first()
    if not scorecard:
        raise HTTPException(status_code=400, detail="Scorecard not found for this requisition")

    candidates = db.query(Candidate).filter(Candidate.is_active == True).all()
    scored_count = 0
    is_demo = not GroqAIService.is_groq_available()

    for cand in candidates:
        score_data = DeterministicScoringEngine.calculate_candidate_score(cand, scorecard)
        # Check if score already exists
        existing = db.query(CandidateScore).filter(
            CandidateScore.candidate_id == cand.id,
            CandidateScore.requisition_id == id
        ).first()

        if existing:
            existing.total_score = score_data["total_score"]
            existing.required_skills_score = score_data["required_skills_score"]
            existing.experience_score = score_data["experience_score"]
            existing.relevant_experience_score = score_data["relevant_experience_score"]
            existing.good_to_have_score = score_data["good_to_have_score"]
            existing.notice_period_score = score_data["notice_period_score"]
            existing.matching_skills = score_data["matching_skills"]
            existing.missing_skills = score_data["missing_skills"]
            existing.match_grade = score_data["match_grade"]
            existing.ai_reasoning = score_data["ai_reasoning"]
            existing.is_demo_score = is_demo
            db.query(ScoreEvidence).filter(ScoreEvidence.candidate_score_id == existing.id).delete()
            for ev in score_data["evidence_items"]:
                ev_model = ScoreEvidence(
                    candidate_score_id=existing.id,
                    criterion_name=ev["criterion_name"],
                    max_score=ev["max_score"],
                    awarded_score=ev["awarded_score"],
                    evidence_quote=ev["evidence_quote"],
                    explanation=ev["explanation"],
                    missing_info=ev.get("missing_info")
                )
                db.add(ev_model)
        else:
            new_score = CandidateScore(
                candidate_id=cand.id,
                requisition_id=id,
                scorecard_id=scorecard.id,
                total_score=score_data["total_score"],
                max_possible_score=score_data["max_possible_score"],
                required_skills_score=score_data["required_skills_score"],
                experience_score=score_data["experience_score"],
                relevant_experience_score=score_data["relevant_experience_score"],
                good_to_have_score=score_data["good_to_have_score"],
                notice_period_score=score_data["notice_period_score"],
                matching_skills=score_data["matching_skills"],
                missing_skills=score_data["missing_skills"],
                match_grade=score_data["match_grade"],
                ai_reasoning=score_data["ai_reasoning"],
                is_demo_score=is_demo
            )
            db.add(new_score)
            db.flush()
            for ev in score_data["evidence_items"]:
                ev_model = ScoreEvidence(
                    candidate_score_id=new_score.id,
                    criterion_name=ev["criterion_name"],
                    max_score=ev["max_score"],
                    awarded_score=ev["awarded_score"],
                    evidence_quote=ev["evidence_quote"],
                    explanation=ev["explanation"],
                    missing_info=ev.get("missing_info")
                )
                db.add(ev_model)

        scored_count += 1

    db.commit()
    return {"message": f"Successfully calculated deterministic scores for {scored_count} candidates"}
