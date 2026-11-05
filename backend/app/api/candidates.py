import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.rbac import get_current_user, require_recruiter
from app.database.session import get_db
from app.models.user import User
from app.models.requisition import Requisition
from app.models.candidate import Candidate, Resume
from app.models.score import CandidateScore
from app.models.audit import AuditLog
from app.schemas.candidate import CandidateResponse

router = APIRouter(tags=["Candidates"])


@router.get("/api/requisitions/{id}/candidates")
def get_requisition_candidates(
    id: int,
    search: Optional[str] = Query(None, description="Search by name, role, skill, or code"),
    min_score: Optional[float] = Query(None, description="Minimum match score filter"),
    match_grade: Optional[str] = Query(None, description="High Match, Moderate Match, Low Match"),
    stage: Optional[str] = Query(None, description="Pipeline stage filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requisition).filter(Requisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")

    # If client hiring manager, check client org
    if current_user.role.value == "client_hiring_manager":
        if req.client_org_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to requisition")

    query = db.query(Candidate).filter(Candidate.is_active == True)

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            (Candidate.first_name.ilike(search_fmt)) |
            (Candidate.last_name.ilike(search_fmt)) |
            (Candidate.candidate_code.ilike(search_fmt)) |
            (Candidate.current_role.ilike(search_fmt))
        )

    if stage:
        query = query.filter(Candidate.current_stage == stage)

    candidates = query.all()

    # Enrich each candidate with score for this requisition
    results = []
    for cand in candidates:
        score_record = db.query(CandidateScore).filter(
            CandidateScore.candidate_id == cand.id,
            CandidateScore.requisition_id == id
        ).order_by(desc(CandidateScore.created_at)).first()

        score_val = score_record.total_score if score_record else 0.0
        grade = score_record.match_grade if score_record else "Unscored"

        # Apply score filters if provided (low scoring candidates still remain searchable!)
        if min_score is not None and score_val < min_score:
            continue
        if match_grade and grade != match_grade:
            continue

        cand_dict = {
            "id": cand.id,
            "candidate_code": cand.candidate_code,
            "first_name": cand.first_name,
            "last_name": cand.last_name,
            "email": cand.email,
            "phone": cand.phone,
            "current_role": cand.current_role,
            "total_experience_years": cand.total_experience_years,
            "relevant_experience_years": cand.relevant_experience_years,
            "skills": cand.skills or [],
            "notice_period_days": cand.notice_period_days,
            "current_location": cand.current_location,
            "education": cand.education,
            "summary": cand.summary,
            "current_stage": cand.current_stage,
            "created_at": cand.created_at.isoformat(),
            "latest_score": {
                "id": score_record.id if score_record else None,
                "total_score": score_val,
                "match_grade": grade,
                "matching_skills": score_record.matching_skills if score_record else [],
                "missing_skills": score_record.missing_skills if score_record else [],
                "ai_reasoning": score_record.ai_reasoning if score_record else None,
                "is_demo_score": score_record.is_demo_score if score_record else False,
            } if score_record else None
        }
        results.append(cand_dict)

    # Rank by score descending (candidates with higher score on top)
    results.sort(key=lambda x: (x["latest_score"]["total_score"] if x["latest_score"] else -1), reverse=True)
    return results


@router.get("/api/candidates/{id}")
def get_candidate(
    id: int,
    requisition_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cand = db.query(Candidate).filter(Candidate.id == id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Record Audit Log: DPDP requirement: Record who viewed candidate profiles and when
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="VIEW_CANDIDATE_PROFILE",
        resource_type="candidate",
        resource_id=cand.candidate_code,
        details={
            "candidate_id": cand.id,
            "viewer_role": current_user.role.value,
            "requisition_id": requisition_id
        }
    )
    db.add(audit)
    db.commit()

    score_query = db.query(CandidateScore).filter(CandidateScore.candidate_id == id)
    if requisition_id:
        score_query = score_query.filter(CandidateScore.requisition_id == requisition_id)
    score_record = score_query.order_by(desc(CandidateScore.created_at)).first()

    resumes = db.query(Resume).filter(Resume.candidate_id == id).all()

    return {
        "id": cand.id,
        "candidate_code": cand.candidate_code,
        "first_name": cand.first_name,
        "last_name": cand.last_name,
        "email": cand.email,
        "phone": cand.phone,
        "current_role": cand.current_role,
        "total_experience_years": cand.total_experience_years,
        "relevant_experience_years": cand.relevant_experience_years,
        "skills": cand.skills or [],
        "notice_period_days": cand.notice_period_days,
        "current_location": cand.current_location,
        "education": cand.education,
        "summary": cand.summary,
        "current_stage": cand.current_stage,
        "raw_text": cand.raw_text,
        "created_at": cand.created_at.isoformat(),
        "resumes": [
            {
                "id": r.id,
                "file_name": r.file_name,
                "file_type": r.file_type,
                "file_size_bytes": r.file_size_bytes,
                "parsing_status": r.parsing_status.value,
                "created_at": r.created_at.isoformat()
            } for r in resumes
        ],
        "latest_score": {
            "id": score_record.id,
            "total_score": score_record.total_score,
            "match_grade": score_record.match_grade,
            "required_skills_score": score_record.required_skills_score,
            "experience_score": score_record.experience_score,
            "relevant_experience_score": score_record.relevant_experience_score,
            "good_to_have_score": score_record.good_to_have_score,
            "notice_period_score": score_record.notice_period_score,
            "matching_skills": score_record.matching_skills,
            "missing_skills": score_record.missing_skills,
            "ai_reasoning": score_record.ai_reasoning,
            "is_demo_score": score_record.is_demo_score
        } if score_record else None
    }


@router.get("/api/candidates/{id}/resume")
def download_or_view_resume(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(Resume.candidate_id == id).order_by(desc(Resume.created_at)).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume record not found")

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="VIEW_ORIGINAL_RESUME",
        resource_type="resume",
        resource_id=resume.file_name,
        details={"candidate_id": id}
    )
    db.add(audit)
    db.commit()

    if resume.file_path and os.path.exists(resume.file_path):
        media_type = "application/pdf" if resume.file_type == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return FileResponse(resume.file_path, media_type=media_type, filename=resume.file_name)
    elif resume.parsed_text:
        return PlainTextResponse(resume.parsed_text)
    else:
        raise HTTPException(status_code=404, detail="Resume file not found on disk")

