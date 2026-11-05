import os
import io
import pytest
from unittest.mock import patch, MagicMock

# Force test database URL BEFORE importing app.main
os.environ["DATABASE_URL"] = "sqlite:///./test_hireai.db"

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.session import get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User, Organization, UserRole
from app.models.requisition import Requisition, JobScorecard, RequisitionStatus
from app.models.candidate import Candidate, Resume, ParsingStatus
from app.models.score import CandidateScore, ScoreEvidence
from app.models.client import ClientSubmission, SubmissionStatus
from app.services.duplicate_detector import DuplicateDetector
from app.services.resume_parser import ResumeParserService
from app.services.scoring_engine import DeterministicScoringEngine
from app.services.groq_service import GroqAIService

# Setup test SQLite in-memory or file database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_hireai.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


from app.main import app
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Create test orgs
    agency = Organization(name="Test Agency", org_type="staffing_agency", client_code="TEST_AGENCY")
    client_org = Organization(name="Test Client Corp", org_type="client", client_code="TEST_CLIENT")
    db.add_all([agency, client_org])
    db.flush()

    # Create recruiter user
    recruiter = User(
        email="test.recruiter@hireai.com",
        hashed_password=hash_password("password123"),
        full_name="Test Recruiter",
        role=UserRole.RECRUITER,
        organization_id=agency.id,
        is_active=True
    )
    # Create client user
    client_user = User(
        email="test.client@testcorp.com",
        hashed_password=hash_password("password123"),
        full_name="Test Client Manager",
        role=UserRole.CLIENT_HIRING_MANAGER,
        organization_id=client_org.id,
        is_active=True
    )
    db.add_all([recruiter, client_user])
    db.flush()

    # Create test requisition
    req = Requisition(
        requisition_code="REQ-TEST-01",
        title="Senior Java Developer",
        department="Engineering",
        location="Noida",
        experience_min=5.0,
        experience_max=8.0,
        max_notice_period_days=60,
        description="Looking for Senior Java Developer with Spring Boot and Microservices experience.",
        status=RequisitionStatus.ACTIVE,
        client_org_id=client_org.id,
        created_by_id=recruiter.id
    )
    db.add(req)
    db.flush()

    card = JobScorecard(
        requisition_id=req.id,
        version=1,
        must_have_skills=["Java", "Spring Boot", "Microservices"],
        good_to_have_skills=["Kafka", "Docker"],
        min_experience=5.0,
        max_experience=8.0,
        max_notice_period=60,
        is_approved=True
    )
    db.add(card)

    # Candidate 1 (High match)
    cand1 = Candidate(
        candidate_code="CND-TEST-01",
        first_name="Ritika",
        last_name="Bansal",
        email="ritika@test.com",
        phone="+91 9876543210",
        current_role="Senior Java Developer",
        total_experience_years=6.5,
        relevant_experience_years=6.0,
        skills=["Java", "Spring Boot", "Microservices", "Kafka"],
        notice_period_days=60,
        current_location="Noida",
        raw_text="Ritika Bansal. Senior Java Developer with 6.5 years experience in Spring Boot and Microservices.",
        current_stage="Parsed"
    )
    # Candidate 2 (Low match)
    cand2 = Candidate(
        candidate_code="CND-TEST-02",
        first_name="Arjun",
        last_name="Rawat",
        email="arjun@test.com",
        phone="+91 9876543211",
        current_role="KYC Analyst",
        total_experience_years=3.0,
        relevant_experience_years=0.0,
        skills=["KYC", "Excel", "AML"],
        notice_period_days=30,
        current_location="Noida",
        raw_text="Arjun Rawat. KYC Analyst with 3 years experience in AML and Excel.",
        current_stage="Parsed"
    )
    db.add_all([cand1, cand2])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    if os.path.exists("./test_hireai.db"):
        try:
            os.remove("./test_hireai.db")
        except Exception:
            pass


def get_auth_token(role="recruiter", user_id=1):
    return create_access_token(data={"sub": str(user_id), "role": role})


# -------------------------------------------------------------
# 1. Authentication Tests
# -------------------------------------------------------------
def test_login_success():
    res = client.post("/api/auth/login", json={"email": "test.recruiter@hireai.com", "password": "password123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "recruiter"


def test_login_invalid_credentials():
    res = client.post("/api/auth/login", json={"email": "test.recruiter@hireai.com", "password": "wrongpassword"})
    assert res.status_code == 401


# -------------------------------------------------------------
# 2. RBAC & Client Data Isolation Tests
# -------------------------------------------------------------
def test_recruiter_can_access_requisitions():
    token = get_auth_token(role="recruiter", user_id=1)
    res = client.get("/api/requisitions", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_client_cannot_create_requisition():
    token = get_auth_token(role="client_hiring_manager", user_id=2)
    res = client.post(
        "/api/requisitions",
        json={"title": "Client unauthorized req", "description": "test", "location": "Noida"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


# -------------------------------------------------------------
# 3. Duplicate Detection Unit Tests
# -------------------------------------------------------------
def test_duplicate_detection_by_hash_and_email():
    db = TestingSessionLocal()
    dummy_bytes = b"Sample resume text for hashing test"
    file_hash = DuplicateDetector.compute_sha256(dummy_bytes)

    # Email match check
    is_dup, reason, _ = DuplicateDetector.check_duplicate(db, file_hash="unseen_hash", email="ritika@test.com")
    assert is_dup is True
    assert "already registered" in reason

    # Unseen candidate
    is_dup, _, _ = DuplicateDetector.check_duplicate(db, file_hash="unseen_hash", email="brand.new@test.com")
    assert is_dup is False
    db.close()


# -------------------------------------------------------------
# 4. Resume Parsing Unit Tests
# -------------------------------------------------------------
def test_resume_parser_docx_and_cleaning():
    cleaned = ResumeParserService.clean_text("  Line 1  \n\n\n  Line 2 with \x00 null byte  ")
    assert "Line 1" in cleaned
    assert "Line 2" in cleaned
    assert "\x00" not in cleaned


# -------------------------------------------------------------
# 5. JD Extraction Validation with Mock
# -------------------------------------------------------------
def test_jd_analysis_mocked():
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="""{
            "must_have_skills": ["Java", "Spring Boot", "Microservices"],
            "good_to_have_skills": ["Docker", "Kubernetes"],
            "min_experience": 5.0,
            "max_experience": 8.0,
            "location": "Noida",
            "max_notice_period": 60,
            "ctc_info": "18 - 25 LPA",
            "suggested_title": "Senior Java Developer",
            "summary": "Role requires 5-8 years experience in Java Spring Boot."
        }"""))
    ]

    with patch("app.services.groq_service.groq_client") as mock_groq:
        mock_groq.chat.completions.create.return_value = mock_response
        with patch.object(GroqAIService, "is_groq_available", return_value=True):
            resp, is_demo = GroqAIService.analyze_job_description("Dummy JD with Java and Spring Boot")
            assert is_demo is False
            assert "Spring Boot" in resp.must_have_skills
            assert resp.min_experience == 5.0


# -------------------------------------------------------------
# 6. Deterministic Candidate Scoring & Evidence Generation
# -------------------------------------------------------------
def test_deterministic_scoring_fairness_and_evidence():
    db = TestingSessionLocal()
    cand = db.query(Candidate).filter(Candidate.candidate_code == "CND-TEST-01").first()
    scorecard = db.query(JobScorecard).filter(JobScorecard.requisition_id == 1).first()

    result = DeterministicScoringEngine.calculate_candidate_score(cand, scorecard)
    assert result["total_score"] >= 80.0
    assert result["match_grade"] == "High Match"
    assert len(result["evidence_items"]) == 5

    # Check evidence quote
    req_skill_ev = next(e for e in result["evidence_items"] if "Required" in e["criterion_name"])
    assert "Spring Boot" in req_skill_ev["evidence_quote"] or "Java" in req_skill_ev["evidence_quote"]
    assert req_skill_ev["awarded_score"] == 40.0

    # Low match check for Candidate 2
    cand2 = db.query(Candidate).filter(Candidate.candidate_code == "CND-TEST-02").first()
    result2 = DeterministicScoringEngine.calculate_candidate_score(cand2, scorecard)
    assert result2["total_score"] < 50.0
    assert result2["match_grade"] == "Low Match"
    db.close()


# -------------------------------------------------------------
# 7. Client Shortlist and Mandatory Rejection Reason
# -------------------------------------------------------------
def test_client_shortlist_and_rejection():
    token = get_auth_token(role="client_hiring_manager", user_id=2)
    db = TestingSessionLocal()
    sub = ClientSubmission(
        requisition_id=1,
        candidate_id=1,
        client_org_id=2,
        status=SubmissionStatus.PENDING_REVIEW
    )
    db.add(sub)
    db.commit()
    sub_id = sub.id
    db.close()

    # Shortlist
    res = client.post(
        f"/api/client/submissions/{sub_id}/shortlist",
        json={"feedback_text": "Candidate matches requirements."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "shortlisted"

    # Rejection without reason fails (mandatory validation)
    res_fail = client.post(
        f"/api/client/submissions/{sub_id}/reject",
        json={"rejection_reason": ""},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_fail.status_code in [400, 422]

    # Rejection with mandatory reason succeeds
    res_succ = client.post(
        f"/api/client/submissions/{sub_id}/reject",
        json={"rejection_reason": "Notice period too long and lacks Docker depth."},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_succ.status_code == 200
    assert res_succ.json()["status"] == "rejected"


# -------------------------------------------------------------
# 8. Pipeline Transitions
# -------------------------------------------------------------
def test_pipeline_transition():
    token = get_auth_token(role="recruiter", user_id=1)
    res = client.patch(
        "/api/candidates/1/pipeline",
        json={"to_stage": "Shortlisted", "notes": "Passed preliminary recruiter phone screen"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["to_stage"] == "Shortlisted"


# -------------------------------------------------------------
# 9. Candidate Deletion Request (DPDP Act Compliance)
# -------------------------------------------------------------
def test_candidate_deletion_request():
    token = get_auth_token(role="recruiter", user_id=1)
    res = client.post(
        "/api/candidates/2/deletion-request",
        json={"reason": "Candidate requested deletion of personal profile"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "completed"

    # Verify candidate is anonymized
    db = TestingSessionLocal()
    cand = db.query(Candidate).filter(Candidate.id == 2).first()
    assert cand.first_name == "Deleted"
    assert cand.is_active is False
    assert "erased" in cand.raw_text.lower()
    db.close()


# -------------------------------------------------------------
# 10. Excel Spreadsheet Bulk Upload & Template
# -------------------------------------------------------------
def test_excel_template_download():
    res = client.get("/api/upload-batches/template/excel")
    assert res.status_code == 200
    assert len(res.content) > 1000
    assert "openxmlformats" in res.headers.get("content-type", "")


def test_excel_bulk_upload():
    from app.services.excel_parser import ExcelCandidateParser
    excel_bytes = ExcelCandidateParser.generate_sample_excel_template()

    token = get_auth_token(role="recruiter", user_id=1)
    files = [
        ("files", ("test_candidates.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
    ]
    res = client.post(
        "/api/requisitions/1/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["parsed_count"] >= 3
    assert data["status"] == "completed"
