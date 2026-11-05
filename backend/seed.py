import os
import sys
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.database.base import Base
from app.database.session import engine
from app.models.user import User, Organization, UserRole
from app.models.requisition import Requisition, JobScorecard, RequisitionStatus
from app.models.candidate import Candidate, Resume, ResumeUploadBatch, BatchStatus, ParsingStatus
from app.models.score import CandidateScore, ScoreEvidence
from app.models.client import ClientSubmission, ClientFeedback, Interview, SubmissionStatus
from app.models.pipeline import CandidatePipelineHistory
from app.models.privacy import CandidateConsent
from app.models.audit import AuditLog
from app.services.resume_parser import ResumeParserService
from app.services.duplicate_detector import DuplicateDetector
from app.services.scoring_engine import DeterministicScoringEngine
from generate_sample_cvs import CANDIDATES_DATA, generate_all_sample_cvs, CVS_DIR


def seed_database():
    print("--- Starting HireAI Production Seed Script ---")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data for clean seed
    for tbl in [
        AuditLog, CandidateConsent, CandidatePipelineHistory, Interview,
        ClientFeedback, ClientSubmission, ScoreEvidence, CandidateScore,
        Resume, ResumeUploadBatch, Candidate, JobScorecard, Requisition,
        User, Organization
    ]:
        db.query(tbl).delete()
    db.commit()

    # 1. Organizations
    agency_org = Organization(
        name="Apex Staffing Solutions",
        org_type="staffing_agency",
        domain="apexstaffing.com",
        client_code="APEX_STAFF"
    )
    client_org = Organization(
        name="FinTech Global Corp",
        org_type="client",
        domain="fintechcorp.com",
        client_code="FINTECH_CORP"
    )
    db.add_all([agency_org, client_org])
    db.flush()

    # 2. Users (Recruiter & Client Hiring Manager)
    recruiter_user = User(
        email="recruiter@hireai.com",
        hashed_password=hash_password("password123"),
        full_name="Sarah Jenkins",
        role=UserRole.RECRUITER,
        organization_id=agency_org.id,
        is_active=True
    )
    client_user = User(
        email="client.hiring@fintechcorp.com",
        hashed_password=hash_password("password123"),
        full_name="Rajesh Khanna",
        role=UserRole.CLIENT_HIRING_MANAGER,
        organization_id=client_org.id,
        is_active=True
    )
    db.add_all([recruiter_user, client_user])
    db.flush()

    # 3. Requisitions
    req_java = Requisition(
        requisition_code="REQ-90110",
        title="Senior Java Developer",
        department="Backend Engineering",
        location="Noida",
        experience_min=5.0,
        experience_max=8.0,
        ctc_min_lpa=18.0,
        ctc_max_lpa=28.0,
        employment_type="Full-Time",
        max_notice_period_days=60,
        description=(
            "We are seeking an experienced Senior Java Developer to design, build, and maintain mission-critical "
            "distributed microservices. Candidate must have 5-8 years of experience with strong hands-on expertise "
            "in Java 17+, Spring Boot, Microservices, and REST APIs. Experience with Apache Kafka, Docker, Kubernetes, "
            "and PostgreSQL is highly preferred. Base location: Noida. Maximum notice period: 60 days."
        ),
        status=RequisitionStatus.ACTIVE,
        client_org_id=client_org.id,
        created_by_id=recruiter_user.id
    )

    req_fe = Requisition(
        requisition_code="REQ-90115",
        title="Frontend Architect",
        department="UI Platform",
        location="Bangalore",
        experience_min=7.0,
        experience_max=10.0,
        ctc_min_lpa=26.0,
        ctc_max_lpa=38.0,
        employment_type="Full-Time",
        max_notice_period_days=30,
        description=(
            "Looking for a seasoned Frontend Architect with 7-10 years experience to spearhead modern web platform "
            "initiatives. Deep expertise in React, TypeScript, Tailwind CSS, system design, performance optimization, "
            "and component library governance is required. Base location: Bangalore. Notice period: 30 days."
        ),
        status=RequisitionStatus.ACTIVE,
        client_org_id=client_org.id,
        created_by_id=recruiter_user.id
    )
    db.add_all([req_java, req_fe])
    db.flush()

    # 4. Job Scorecards
    scorecard_java = JobScorecard(
        requisition_id=req_java.id,
        version=1,
        must_have_skills=["Java", "Spring Boot", "Microservices"],
        good_to_have_skills=["Kafka", "Docker", "Kubernetes", "PostgreSQL"],
        min_experience=5.0,
        max_experience=8.0,
        location="Noida",
        max_notice_period=60,
        ctc_info="18 - 28 LPA",
        weights={
            "required_skills": 40.0,
            "experience_match": 25.0,
            "relevant_experience": 15.0,
            "good_to_have_skills": 10.0,
            "notice_period": 10.0
        },
        is_approved=True
    )

    scorecard_fe = JobScorecard(
        requisition_id=req_fe.id,
        version=1,
        must_have_skills=["React", "TypeScript", "Tailwind", "System Architecture"],
        good_to_have_skills=["Next.js", "Redux", "GraphQL", "CI/CD"],
        min_experience=7.0,
        max_experience=10.0,
        location="Bangalore",
        max_notice_period=30,
        ctc_info="26 - 38 LPA",
        weights={
            "required_skills": 40.0,
            "experience_match": 25.0,
            "relevant_experience": 15.0,
            "good_to_have_skills": 10.0,
            "notice_period": 10.0
        },
        is_approved=True
    )
    db.add_all([scorecard_java, scorecard_fe])
    db.flush()

    # 5. Upload Batch
    batch = ResumeUploadBatch(
        batch_code="BATCH-INITIAL-001",
        requisition_id=req_java.id,
        total_files=len(CANDIDATES_DATA),
        parsed_count=len(CANDIDATES_DATA),
        failed_count=0,
        duplicate_count=0,
        status=BatchStatus.COMPLETED
    )
    db.add(batch)
    db.flush()

    # Make sure sample CVs are on disk
    generate_all_sample_cvs()

    # 6. Parse and Seed Candidates & Resumes
    created_candidates = []
    for cand_meta in CANDIDATES_DATA:
        filename = f"{cand_meta['code']}_{cand_meta['first_name']}_{cand_meta['last_name']}.{cand_meta['file_ext']}"
        filepath = os.path.join(CVS_DIR, filename)

        with open(filepath, "rb") as f_in:
            file_bytes = f_in.read()

        file_hash = DuplicateDetector.compute_sha256(file_bytes)
        raw_text, ocr_applied, file_type = ResumeParserService.parse_resume(file_bytes, filename)

        # Stage mapping for realistic pipeline spread
        default_stage = "Parsed"
        if cand_meta["code"] in ["CND-91022", "CND-91105"]:
            default_stage = "Submitted to Client"
        elif cand_meta["code"] == "CND-91180":
            default_stage = "Client Approved"
        elif cand_meta["code"] == "CND-91240":
            default_stage = "Interview Scheduled"
        elif cand_meta["code"] == "CND-91088":
            default_stage = "Screened"
        elif cand_meta["code"] == "CND-91047":
            default_stage = "Parsed"
        elif cand_meta["code"] == "CND-91285":
            default_stage = "Shortlisted"

        candidate = Candidate(
            candidate_code=cand_meta["code"],
            first_name=cand_meta["first_name"],
            last_name=cand_meta["last_name"],
            email=cand_meta["email"],
            phone=cand_meta["phone"],
            current_role=cand_meta["role"],
            total_experience_years=cand_meta["total_exp"],
            relevant_experience_years=cand_meta["rel_exp"],
            skills=cand_meta["skills"],
            notice_period_days=cand_meta["notice"],
            current_location=cand_meta["location"],
            education=cand_meta["education"],
            summary=f"{cand_meta['role']} with {cand_meta['total_exp']} years total experience and verified skill highlights.",
            raw_text=raw_text,
            current_stage=default_stage,
            is_active=True
        )
        db.add(candidate)
        db.flush()
        created_candidates.append(candidate)

        # Resume record
        resume = Resume(
            candidate_id=candidate.id,
            requisition_id=req_java.id,
            batch_id=batch.id,
            file_name=filename,
            file_path=filepath,
            file_hash=file_hash,
            file_type=file_type,
            file_size_bytes=len(file_bytes),
            parsed_text=raw_text,
            parsing_status=ParsingStatus.PARSED,
            ocr_applied=ocr_applied
        )
        db.add(resume)

        # Candidate DPDP Consent
        consent = CandidateConsent(
            candidate_id=candidate.id,
            consent_given=True,
            consent_timestamp=datetime.utcnow() - timedelta(days=5),
            purpose_of_processing="Recruitment evaluation, scorecard matching and client submission",
            valid_until=datetime.utcnow() + timedelta(days=360),
            notes="Captured during initial sourcing application"
        )
        db.add(consent)

        # Pipeline history initial entry
        history_init = CandidatePipelineHistory(
            candidate_id=candidate.id,
            requisition_id=req_java.id,
            from_stage="Sourced",
            to_stage=default_stage,
            changed_by_id=recruiter_user.id,
            notes="Uploaded in initial seed batch and screened"
        )
        db.add(history_init)

        # Deterministic Score against Java Scorecard
        score_data = DeterministicScoringEngine.calculate_candidate_score(candidate, scorecard_java)
        cand_score = CandidateScore(
            candidate_id=candidate.id,
            requisition_id=req_java.id,
            scorecard_id=scorecard_java.id,
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

        # Score Evidence items directly from file text!
        for ev in score_data["evidence_items"]:
            evidence_rec = ScoreEvidence(
                candidate_score_id=cand_score.id,
                criterion_name=ev["criterion_name"],
                max_score=ev["max_score"],
                awarded_score=ev["awarded_score"],
                evidence_quote=ev["evidence_quote"],
                explanation=ev["explanation"],
                missing_info=ev.get("missing_info")
            )
            db.add(evidence_rec)

    # 7. Seed Client Submissions & Feedback
    # Submit Ritika Bansal (CND-91022) to Client
    cand_ritika = next(c for c in created_candidates if c.candidate_code == "CND-91022")
    sub_ritika = ClientSubmission(
        requisition_id=req_java.id,
        candidate_id=cand_ritika.id,
        client_org_id=client_org.id,
        submitted_by_id=recruiter_user.id,
        status=SubmissionStatus.PENDING_REVIEW,
        recruiter_notes="Strong profile with 6.5 yrs Java & Spring Boot experience. Directly relevant background.",
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    db.add(sub_ritika)

    # Submit Vikram Malhotra (CND-91105) with shortlist feedback
    cand_vikram = next(c for c in created_candidates if c.candidate_code == "CND-91105")
    sub_vikram = ClientSubmission(
        requisition_id=req_java.id,
        candidate_id=cand_vikram.id,
        client_org_id=client_org.id,
        submitted_by_id=recruiter_user.id,
        status=SubmissionStatus.SHORTLISTED,
        recruiter_notes="High scoring candidate with Kafka, Docker, and Kubernetes expertise.",
        reviewed_by_id=client_user.id,
        reviewed_at=datetime.utcnow() - timedelta(hours=18),
        created_at=datetime.utcnow() - timedelta(days=3)
    )
    db.add(sub_vikram)
    db.flush()

    fb_vikram = ClientFeedback(
        submission_id=sub_vikram.id,
        client_user_id=client_user.id,
        action="shortlist",
        feedback_text="Strong candidate. Cloud native architecture and Spring Boot experience match our microservices roadmap."
    )
    db.add(fb_vikram)

    # Submit Divya Venkatesh (CND-91180) with interview request
    cand_divya = next(c for c in created_candidates if c.candidate_code == "CND-91180")
    sub_divya = ClientSubmission(
        requisition_id=req_java.id,
        candidate_id=cand_divya.id,
        client_org_id=client_org.id,
        submitted_by_id=recruiter_user.id,
        status=SubmissionStatus.INTERVIEW_REQUESTED,
        recruiter_notes="8 years experience with AWS and payment gateway architecture.",
        reviewed_by_id=client_user.id,
        reviewed_at=datetime.utcnow() - timedelta(hours=8),
        created_at=datetime.utcnow() - timedelta(days=4)
    )
    db.add(sub_divya)
    db.flush()

    interview_time = datetime.utcnow() + timedelta(days=2, hours=4)
    interview_divya = Interview(
        submission_id=sub_divya.id,
        candidate_id=cand_divya.id,
        round_name="Technical Round 1",
        scheduled_time=interview_time,
        interviewer_name="Rajesh Khanna (Technical Lead)",
        meeting_link="https://meet.google.com/hireai-fintech-interview",
        status="scheduled"
    )
    db.add(interview_divya)

    # Submit Pooja Nair (CND-91088) with client rejection demonstrating mandatory reason requirement
    cand_pooja = next(c for c in created_candidates if c.candidate_code == "CND-91088")
    sub_pooja = ClientSubmission(
        requisition_id=req_java.id,
        candidate_id=cand_pooja.id,
        client_org_id=client_org.id,
        submitted_by_id=recruiter_user.id,
        status=SubmissionStatus.REJECTED,
        recruiter_notes="Java developer with Hibernate experience.",
        reviewed_by_id=client_user.id,
        reviewed_at=datetime.utcnow() - timedelta(days=1),
        created_at=datetime.utcnow() - timedelta(days=3)
    )
    db.add(sub_pooja)
    db.flush()

    fb_pooja = ClientFeedback(
        submission_id=sub_pooja.id,
        client_user_id=client_user.id,
        action="reject",
        rejection_reason="Notice period of 90 days exceeds maximum 60 days limit and candidate lacks required Spring Boot / Microservices depth.",
        feedback_text="Immediate requirement for Q1 release; notice period cannot be accommodated."
    )
    db.add(fb_pooja)

    # 8. Seed Audit Logs
    audit_entries = [
        AuditLog(
            user_id=recruiter_user.id,
            user_email=recruiter_user.email,
            user_role="recruiter",
            action="CREATE_REQUISITION",
            resource_type="requisition",
            resource_id="REQ-90110",
            details={"title": "Senior Java Developer", "location": "Noida"}
        ),
        AuditLog(
            user_id=recruiter_user.id,
            user_email=recruiter_user.email,
            user_role="recruiter",
            action="BULK_RESUME_UPLOAD",
            resource_type="batch",
            resource_id="BATCH-INITIAL-001",
            details={"total_files": 16, "parsed": 16}
        ),
        AuditLog(
            user_id=client_user.id,
            user_email=client_user.email,
            user_role="client_hiring_manager",
            action="CLIENT_SHORTLIST_CANDIDATE",
            resource_type="submission",
            resource_id=str(sub_vikram.id),
            details={"candidate_code": "CND-91105", "action": "shortlist"}
        ),
        AuditLog(
            user_id=client_user.id,
            user_email=client_user.email,
            user_role="client_hiring_manager",
            action="CLIENT_REJECT_CANDIDATE",
            resource_type="submission",
            resource_id=str(sub_pooja.id),
            details={"candidate_code": "CND-91088", "reason": fb_pooja.rejection_reason}
        )
    ]
    db.add_all(audit_entries)

    db.commit()
    db.close()
    print("--- Successfully seeded HireAI database with authentic sample data! ---")


if __name__ == "__main__":
    seed_database()

