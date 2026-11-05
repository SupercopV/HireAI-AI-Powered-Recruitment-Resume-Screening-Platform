import os
import random
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.rbac import require_recruiter
from app.database.session import get_db
from app.models.user import User
from app.models.requisition import Requisition, JobScorecard
from app.models.candidate import Candidate, Resume, ResumeUploadBatch, BatchStatus, ParsingStatus
from app.models.score import CandidateScore, ScoreEvidence
from app.models.pipeline import CandidatePipelineHistory
from app.models.privacy import CandidateConsent
from app.models.audit import AuditLog
from app.schemas.candidate import BatchResponse
from app.services.resume_parser import ResumeParserService
from app.services.duplicate_detector import DuplicateDetector
from app.services.groq_service import GroqAIService
from app.services.scoring_engine import DeterministicScoringEngine
from app.services.excel_parser import ExcelCandidateParser
from fastapi.responses import Response

router = APIRouter(tags=["Resumes & Uploads"])


@router.get("/api/upload-batches/template/excel")
def download_excel_template():
    """
    Download a formatted Excel spreadsheet template (.xlsx) for bulk resume upload.
    """
    excel_bytes = ExcelCandidateParser.generate_sample_excel_template()
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=hireai_candidate_batch_template.xlsx"}
    )


@router.post("/api/requisitions/{id}/upload", response_model=BatchResponse)
async def upload_resumes(
    id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    req = db.query(Requisition).filter(Requisition.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")

    if len(files) > settings.MAX_CV_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Upload batch exceeds maximum limit of {settings.MAX_CV_BATCH_SIZE} files"
        )

    scorecard = db.query(JobScorecard).filter(JobScorecard.requisition_id == id).order_by(JobScorecard.version.desc()).first()

    batch_code = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
    batch = ResumeUploadBatch(
        batch_code=batch_code,
        requisition_id=id,
        total_files=len(files),
        status=BatchStatus.PROCESSING
    )
    db.add(batch)
    db.flush()

    parsed_count = 0
    failed_count = 0
    duplicate_count = 0

    req_upload_dir = os.path.join(settings.UPLOAD_DIR, f"req_{id}")
    os.makedirs(req_upload_dir, exist_ok=True)

    for file in files:
        file_bytes = await file.read()
        file_size = len(file_bytes)

        # File size check (e.g., 25MB max)
        if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            failed_count += 1
            res = Resume(
                requisition_id=id,
                batch_id=batch.id,
                file_name=file.filename or "unknown",
                file_path="",
                file_hash="",
                file_size_bytes=file_size,
                parsing_status=ParsingStatus.FAILED,
                parsing_error=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )
            db.add(res)
            continue

        file_hash = DuplicateDetector.compute_sha256(file_bytes)
        
        # Check if file is a spreadsheet (.xlsx, .xls, .csv)
        lower_filename = (file.filename or "").lower()
        if lower_filename.endswith((".xlsx", ".xls", ".csv")):
            try:
                sheet_candidates = ExcelCandidateParser.parse_spreadsheet(file_bytes, file.filename or "")
                
                # Save spreadsheet file to disk
                safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
                file_save_path = os.path.join(req_upload_dir, safe_filename)
                with open(file_save_path, "wb") as f_out:
                    f_out.write(file_bytes)

                for cand_data in sheet_candidates:
                    email = cand_data.get("email")
                    phone = cand_data.get("phone")
                    row_hash = DuplicateDetector.compute_sha256((f"{email}_{phone}_{cand_data.get('first_name')}").encode())

                    is_dup, dup_reason, existing_cand = DuplicateDetector.check_duplicate(
                        db, file_hash=row_hash, email=email, phone=phone
                    )
                    if is_dup:
                        duplicate_count += 1
                        res = Resume(
                            candidate_id=existing_cand.id if existing_cand else None,
                            requisition_id=id,
                            batch_id=batch.id,
                            file_name=f"{cand_data.get('first_name')}_{cand_data.get('last_name')}_(Sheet)",
                            file_path=file_save_path,
                            file_hash=row_hash,
                            file_type="excel_row",
                            file_size_bytes=len(cand_data.get("raw_text", "").encode()),
                            parsing_status=ParsingStatus.DUPLICATE,
                            parsing_error=dup_reason
                        )
                        db.add(res)
                        continue

                    # Create Candidate from spreadsheet row
                    cand_code = f"CND-{random.randint(90000, 99999)}"
                    raw_text = cand_data.get("raw_text", "")
                    new_candidate = Candidate(
                        candidate_code=cand_code,
                        first_name=cand_data.get("first_name", "Candidate"),
                        last_name=cand_data.get("last_name", "Applicant"),
                        email=email,
                        phone=phone,
                        current_role=cand_data.get("current_role", "Software Engineer"),
                        total_experience_years=float(cand_data.get("total_experience_years", 0.0)),
                        relevant_experience_years=float(cand_data.get("relevant_experience_years", 0.0)),
                        skills=cand_data.get("skills", []),
                        notice_period_days=int(cand_data.get("notice_period_days", 30)),
                        current_location=cand_data.get("current_location", "Noida"),
                        education=cand_data.get("education", ""),
                        summary=cand_data.get("summary", ""),
                        raw_text=raw_text,
                        current_stage="Parsed"
                    )
                    db.add(new_candidate)
                    db.flush()

                    res = Resume(
                        candidate_id=new_candidate.id,
                        requisition_id=id,
                        batch_id=batch.id,
                        file_name=f"{cand_data.get('first_name')}_{cand_data.get('last_name')} ({file.filename})",
                        file_path=file_save_path,
                        file_hash=row_hash,
                        file_type="excel",
                        file_size_bytes=len(raw_text.encode()),
                        parsed_text=raw_text,
                        parsing_status=ParsingStatus.PARSED
                    )
                    db.add(res)

                    hist = CandidatePipelineHistory(
                        candidate_id=new_candidate.id,
                        requisition_id=id,
                        from_stage="Sourced",
                        to_stage="Parsed",
                        changed_by_id=current_user.id,
                        notes=f"Imported from Excel spreadsheet: {file.filename}"
                    )
                    db.add(hist)

                    consent = CandidateConsent(
                        candidate_id=new_candidate.id,
                        consent_given=True,
                        purpose_of_processing=f"Recruitment screening for {req.title} via Excel spreadsheet batch",
                        notes=f"Imported from batch spreadsheet {file.filename}"
                    )
                    db.add(consent)

                    if scorecard:
                        score_data = DeterministicScoringEngine.calculate_candidate_score(new_candidate, scorecard)
                        cand_score = CandidateScore(
                            candidate_id=new_candidate.id,
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
                            is_demo_score=False
                        )
                        db.add(cand_score)
                        db.flush()

                        for ev in score_data["evidence_items"]:
                            ev_model = ScoreEvidence(
                                candidate_score_id=cand_score.id,
                                criterion_name=ev["criterion_name"],
                                max_score=ev["max_score"],
                                awarded_score=ev["awarded_score"],
                                evidence_quote=ev["evidence_quote"],
                                explanation=ev["explanation"],
                                missing_info=ev.get("missing_info")
                            )
                            db.add(ev_model)

                    parsed_count += 1
                continue
            except Exception as sheet_err:
                failed_count += 1
                res = Resume(
                    requisition_id=id,
                    batch_id=batch.id,
                    file_name=file.filename or "unknown",
                    file_path="",
                    file_hash=file_hash,
                    file_type="excel",
                    file_size_bytes=file_size,
                    parsing_status=ParsingStatus.FAILED,
                    parsing_error=f"Failed to parse spreadsheet: {str(sheet_err)}"
                )
                db.add(res)
                continue

        # 1. Duplicate check by file hash (for PDF / DOCX)
        is_dup, dup_reason, existing_cand = DuplicateDetector.check_duplicate(db, file_hash=file_hash)
        if is_dup:
            duplicate_count += 1
            res = Resume(
                candidate_id=existing_cand.id if existing_cand else None,
                requisition_id=id,
                batch_id=batch.id,
                file_name=file.filename or "unknown",
                file_path="",
                file_hash=file_hash,
                file_size_bytes=file_size,
                parsing_status=ParsingStatus.DUPLICATE,
                parsing_error=dup_reason
            )
            db.add(res)
            continue

        # Save file to disk
        safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        file_save_path = os.path.join(req_upload_dir, safe_filename)
        with open(file_save_path, "wb") as f_out:
            f_out.write(file_bytes)

        # 2. Parse text from file
        try:
            raw_text, ocr_applied, file_type = ResumeParserService.parse_resume(file_bytes, file.filename or "")
        except Exception as parse_err:
            failed_count += 1
            res = Resume(
                requisition_id=id,
                batch_id=batch.id,
                file_name=file.filename or "unknown",
                file_path=file_save_path,
                file_hash=file_hash,
                file_type=file.filename.split(".")[-1].lower() if file.filename else "pdf",
                file_size_bytes=file_size,
                parsing_status=ParsingStatus.FAILED,
                parsing_error=str(parse_err)
            )
            db.add(res)
            continue

        # 3. Extract candidate information via AI / rule extractor
        cand_data, is_demo = GroqAIService.extract_candidate_from_cv(raw_text, file_name=file.filename or "")

        # Check secondary duplicate by email / phone
        email = cand_data.get("email")
        phone = cand_data.get("phone")
        is_contact_dup, contact_dup_reason, existing_cand = DuplicateDetector.check_duplicate(
            db, file_hash=file_hash, email=email, phone=phone
        )
        if is_contact_dup and existing_cand:
            duplicate_count += 1
            res = Resume(
                candidate_id=existing_cand.id,
                requisition_id=id,
                batch_id=batch.id,
                file_name=file.filename or "unknown",
                file_path=file_save_path,
                file_hash=file_hash,
                file_type=file_type,
                file_size_bytes=file_size,
                parsed_text=raw_text,
                parsing_status=ParsingStatus.DUPLICATE,
                parsing_error=contact_dup_reason,
                ocr_applied=ocr_applied
            )
            db.add(res)
            continue

        # Create new Candidate record
        cand_code = f"CND-{random.randint(90000, 99999)}"
        new_candidate = Candidate(
            candidate_code=cand_code,
            first_name=cand_data.get("first_name", "Candidate"),
            last_name=cand_data.get("last_name", "Applicant"),
            email=email,
            phone=phone,
            current_role=cand_data.get("current_role", "Software Engineer"),
            total_experience_years=float(cand_data.get("total_experience_years", 0.0)),
            relevant_experience_years=float(cand_data.get("relevant_experience_years", 0.0)),
            skills=cand_data.get("skills", []),
            notice_period_days=int(cand_data.get("notice_period_days", 30)),
            current_location=cand_data.get("current_location", "Noida"),
            education=cand_data.get("education", ""),
            summary=cand_data.get("summary", ""),
            raw_text=raw_text,
            current_stage="Parsed"
        )
        db.add(new_candidate)
        db.flush()

        # Create Resume record
        res = Resume(
            candidate_id=new_candidate.id,
            requisition_id=id,
            batch_id=batch.id,
            file_name=file.filename or "unknown",
            file_path=file_save_path,
            file_hash=file_hash,
            file_type=file_type,
            file_size_bytes=file_size,
            parsed_text=raw_text,
            parsing_status=ParsingStatus.PARSED,
            ocr_applied=ocr_applied
        )
        db.add(res)

        # Initial Candidate pipeline history
        hist = CandidatePipelineHistory(
            candidate_id=new_candidate.id,
            requisition_id=id,
            from_stage="Sourced",
            to_stage="Parsed",
            changed_by_id=current_user.id,
            notes="Uploaded in bulk batch and successfully parsed"
        )
        db.add(hist)

        # Record DPDP Candidate Consent
        consent = CandidateConsent(
            candidate_id=new_candidate.id,
            consent_given=True,
            purpose_of_processing=f"Recruitment screening for {req.title} at {req.requisition_code}",
            notes="Consent captured upon CV processing"
        )
        db.add(consent)

        # Automatically compute deterministic score if scorecard exists
        if scorecard:
            score_data = DeterministicScoringEngine.calculate_candidate_score(new_candidate, scorecard)
            cand_score = CandidateScore(
                candidate_id=new_candidate.id,
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
            db.add(cand_score)
            db.flush()

            for ev in score_data["evidence_items"]:
                ev_model = ScoreEvidence(
                    candidate_score_id=cand_score.id,
                    criterion_name=ev["criterion_name"],
                    max_score=ev["max_score"],
                    awarded_score=ev["awarded_score"],
                    evidence_quote=ev["evidence_quote"],
                    explanation=ev["explanation"],
                    missing_info=ev.get("missing_info")
                )
                db.add(ev_model)

        parsed_count += 1

    batch.parsed_count = parsed_count
    batch.failed_count = failed_count
    batch.duplicate_count = duplicate_count
    batch.status = BatchStatus.COMPLETED

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="BULK_RESUME_UPLOAD",
        resource_type="batch",
        resource_id=batch.batch_code,
        details={
            "requisition_id": id,
            "total_files": len(files),
            "parsed": parsed_count,
            "failed": failed_count,
            "duplicates": duplicate_count
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/api/upload-batches/{id}", response_model=BatchResponse)
def get_upload_batch(
    id: int,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    batch = db.query(ResumeUploadBatch).filter(ResumeUploadBatch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Upload batch not found")
    return batch


@router.post("/api/upload-batches/{id}/retry", response_model=BatchResponse)
def retry_failed_resumes(
    id: int,
    current_user: User = Depends(require_recruiter),
    db: Session = Depends(get_db)
):
    batch = db.query(ResumeUploadBatch).filter(ResumeUploadBatch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Upload batch not found")

    failed_resumes = db.query(Resume).filter(
        Resume.batch_id == id,
        Resume.parsing_status == ParsingStatus.FAILED
    ).all()

    for res in failed_resumes:
        if res.file_path and os.path.exists(res.file_path):
            try:
                with open(res.file_path, "rb") as f_in:
                    f_bytes = f_in.read()
                raw_text, ocr_applied, _ = ResumeParserService.parse_resume(f_bytes, res.file_name)
                res.parsed_text = raw_text
                res.parsing_status = ParsingStatus.PARSED
                res.parsing_error = None
                res.ocr_applied = ocr_applied
                batch.failed_count = max(0, batch.failed_count - 1)
                batch.parsed_count += 1
            except Exception as e:
                res.parsing_error = f"Retry failed: {str(e)}"

    db.commit()
    db.refresh(batch)
    return batch

