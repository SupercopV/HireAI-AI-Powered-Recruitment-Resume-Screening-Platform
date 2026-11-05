# Technical Design Document (TDD) – HireAI
## Intelligent Recruitment & Candidate Shortlisting Platform

**Repository URL**: `https://github.com/hireai-enterprise/hireai`  
**Live Application Target**: Frontend on Vercel | Backend on Render | Database on Hosted PostgreSQL  
**Document Version**: 1.0.0 (Production Release)  
**Author**: Antigravity Full-Stack & AI Engineering Team  

---

## 1. Executive Summary & Product Architecture

HireAI is an enterprise recruitment management platform designed for staffing agencies to automate manual resume screening, extract structured job scorecards from unstructured text using LLMs, ingest resumes in bulk (up to 500 files per batch) with PDF, DOCX, and OCR fallback processing, deterministically score candidates with verifiable evidence quotations, and share privacy-masked candidate shortlists with client hiring managers.

```
                                    +-------------------------------------------------------------+
                                    |                 HireAI Web Application (React)              |
                                    |   - Recruiter Dashboard & Analytics                         |
                                    |   - Interactive JD Scorecard Builder (Groq Extraction)      |
                                    |   - Bulk CV Drag-and-Drop Uploader (PyMuPDF / docx / OCR)   |
                                    |   - AI-Ranked Candidate List (Explainable Evidence Modal)   |
                                    |   - Client Review Portal (Masked PII, Shortlist, Reject)    |
                                    |   - 11-Stage Recruitment Pipeline (Kanban Lifecycle)        |
                                    |   - DPDP Act Candidate Consent & Erasure Management         |
                                    +------------------------------+------------------------------+
                                                                   |  JSON / REST API / Bearer JWT
                                                                   v
                                    +-------------------------------------------------------------+
                                    |                    FastAPI Backend Engine                   |
                                    |   - OAuth2 / JWT Auth Middleware with RBAC                  |
                                    |   - SHA-256 & Contact Duplicate Detection Service           |
                                    |   - PyMuPDF & python-docx Extraction with Tesseract OCR     |
                                    |   - Deterministic Python Candidate Scoring Engine (0-100)   |
                                    |   - Groq AI Cloud Service (llama-3.3-70b-versatile)         |
                                    |   - Audit Logging & Client Isolation Middleware             |
                                    +------------------------------+------------------------------+
                                                                   |
                                    +------------------------------+------------------------------+
                                    |                                                             |
                                    v                                                             v
        +----------------------------------------+                    +----------------------------------------+
        |         PostgreSQL Database            |                    |             Groq Cloud API             |
        |  - 16 Normalized Tables (Alembic)     |                    |  - Llama-3.3-70B-Versatile             |
        |  - Users, Orgs, Requisitions, Scores   |                    |  - Structured Pydantic Extraction      |
        |  - Evidences, Submissions, Audits      |                    |  - Temperature 0.1 for precision       |
        +----------------------------------------+                    +----------------------------------------+
```

---

## 2. Technology Choices and Justifications

| Layer | Technology | Justification |
| :--- | :--- | :--- |
| **Frontend Framework** | React 19 + Vite | Ultra-fast HMR, component modularity, instant bundling (928ms build), seamless deployment on Vercel. |
| **Styling & Icons** | Tailwind CSS v4 + Lucide React | Clean enterprise design system inspired by Linear, Stripe, and Vercel. Consistent slate/navy typography, custom scrollbars, responsive layouts. |
| **Data Visualization** | Recharts | Performant SVG-based responsive bar and pipeline charts for weekly recruitment analytics. |
| **Backend Framework** | Python 3.11+ & FastAPI | Async native ASGI runtime, automatic OpenAPI/Swagger documentation, strict type-checking, high-throughput I/O. |
| **Data Validation** | Pydantic v2 & Pydantic-Settings | Strict schema enforcement, input sanitization, and structured JSON extraction validation for LLM outputs. |
| **Database & ORM** | PostgreSQL 18 + SQLAlchemy 2.0 | ACIDC transactional compliance, relational integrity, foreign key cascades, JSONB column support, and pool pre-pinging. |
| **Migrations** | Alembic | Version-controlled declarative schema migrations with auto-generation and head stamping. |
| **Authentication** | JWT (`python-jose`) + `bcrypt` | Stateless, cryptographically signed Bearer tokens with 24-hour expiration and 12-round salted password hashes. |
| **Document Extraction** | PyMuPDF (`pymupdf`) + `python-docx` | Native C++ MuPDF engine delivers 10x faster PDF parsing than pypdf; `python-docx` handles complex XML tables. |
| **OCR Fallback** | Tesseract (`pytesseract`) + Pillow | Rescues scanned image-based PDFs when text density is under 40 characters. |
| **AI LLM Extraction** | Groq API (`llama-3.3-70b-versatile`) | Extreme inference speed (< 500ms token generation), deterministic structured JSON output via `response_format={"type": "json_object"}`. |

---

## 3. Normalized Database Schema (16 Tables)

1. **`organizations`**: Multi-tenant organizations (staffing agencies vs. client companies). Includes `client_code`, `domain`, and `org_type`.
2. **`users`**: Platform users with hashed passwords, active flags, and `UserRole` (`recruiter`, `client_hiring_manager`, `admin`).
3. **`requisitions`**: Job requisitions with codes (`REQ-XXXXX`), department, location, experience range, CTC budget, notice period, and status.
4. **`job_scorecards`**: Scorecards tied to requisitions with version control, `must_have_skills` (JSON), `good_to_have_skills` (JSON), and configurable scoring weights.
5. **`candidates`**: Candidate records (`CND-XXXXX`), contact info, role, total experience, relevant experience, verified skills, and raw CV text.
6. **`resumes`**: File storage metadata, SHA-256 hashes, file type, byte size, parsing status (`parsed`, `failed`, `duplicate`), and OCR application flags.
7. **`resume_upload_batches`**: Bulk ingestion tracking (`BATCH-XXXXX`), batch size, success, failure, and duplicate counts.
8. **`candidate_scores`**: Deterministic score records (0–100), sub-scores, matching skills, missing skills, grade (`High`, `Moderate`, `Low`), and reasoning.
9. **`score_evidences`**: Explainable audit records linking each criterion to verbatim quotations from the original resume.
10. **`client_submissions`**: Submissions of candidates from recruiters to specific client organizations, with status and recruiter notes.
11. **`client_feedbacks`**: Feedback records from client hiring managers with mandatory rejection reasons or shortlist notes.
12. **`interviews`**: Scheduled interview rounds with candidate, interviewer, proposed time, and meeting links.
13. **`candidate_pipeline_history`**: Immutable lifecycle logs tracking movements between the 11 recruitment stages.
14. **`candidate_consents`**: DPDP Act compliance records capturing explicit candidate consent, processing purpose, and validity timestamps.
15. **`candidate_deletion_requests`**: DPDP Right-to-Erasure workflow records capturing requests, execution timestamps, and reasons.
16. **`audit_logs`**: Immutable security logs recording every user action, resource access, and candidate profile view.

---

## 4. Main Platform Workflows

### A. Job Scorecard Extraction & Approval
1. Recruiter creates a requisition with a job description.
2. Recruiter clicks **"Extract Criteria via Groq AI"**.
3. FastAPI calls Groq (`llama-3.3-70b-versatile`, temperature 0.1) with system instructions for JSON extraction.
4. Extracted criteria populate editable frontend fields: must-have skills, secondary skills, experience range, notice limit, and scoring weights.
5. Recruiter modifies any field and clicks **"Approve Scorecard"**, locking version 1 in PostgreSQL.

### B. Bulk Resume Parsing & Duplicate Ingestion
1. Recruiter drops up to 500 PDF/DOCX files into the dropzone.
2. Backend computes SHA-256 hash for every file to detect duplicate files instantly.
3. PyMuPDF or python-docx extracts raw text; if text length < 40 characters, Tesseract OCR fallback triggers.
4. Groq parses structured candidate info (or deterministic fallback parser if offline).
5. Secondary duplicate check matches normalized email and 10-digit phone number.
6. New candidates and resumes are committed to PostgreSQL, and candidate consent records are created.
7. Immediate initial scoring is automatically computed against the active scorecard.

### C. Deterministic Scoring & Verbatim Evidence Audit
1. Python scoring engine evaluates candidate data against approved scorecard criteria:
   - **Required Skills (40 pts)**: Proportional to fraction of must-have skills verified.
   - **Experience Match (25 pts)**: Full points if within range; graded linear shortfall penalty.
   - **Relevant Domain Experience (15 pts)**: Proportional to relevant years vs required minimum.
   - **Good-to-Have Skills (10 pts)**: Proportional to secondary skills matched.
   - **Notice Period Availability (10 pts)**: Full points if <= max threshold; graded penalty for excess.
2. For each criterion, `extract_evidence_quote` searches the original CV text for verbatim sentences.
3. If no mention exists, it strictly outputs `"Evidence not found"`. No quotations are ever fabricated.
4. Candidates with score >= 80 receive "High Match", 50–79 "Moderate Match", < 50 "Low Match".
5. All candidates remain searchable; AI never auto-rejects.

### D. Client Review Portal & Mandatory Rejection
1. Recruiter reviews candidate and clicks **"Submit to Client"** with endorsement notes.
2. Client Hiring Manager logs in; backend isolates visibility strictly to submissions for their organization.
3. Candidate personal contact info (email, phone) is masked (`r***@***.com`, `+91 ******910`).
4. Client can:
   - **Shortlist Profile**: updates status and notifies recruiter.
   - **Propose Interview**: chooses date, time, and interviewer.
   - **Reject Profile**: requires a **mandatory rejection reason** (validated in backend, min 3 chars).

### E. DPDP Act 2023 Compliance & Erasure
1. Consent timestamps and purpose limitations are permanently recorded.
2. Profile view events are logged in `audit_logs` (who viewed which candidate and when).
3. Right-to-Erasure workflow anonymizes candidate personal data to `Deleted User`, wipes contact details, erases raw text, and deletes stored CV files from disk.

---

## 5. Algorithmic Fairness & Security Decisions

1. **Fairness Isolation**: The scoring engine never accepts, parses, or factors candidate name, gender, age, photograph, marital status, religion, caste, or personal characteristics.
2. **Deterministic Calculation**: Numerical scores are computed in Python arithmetic, never hallucinated by an LLM prompt.
3. **No Automatic Rejections**: Low-scoring candidates are never discarded; recruiters retain full discretion.
4. **Mandatory Client Rejection Reasons**: Eliminates arbitrary dismissals and creates transparent audit trails.
5. **Anti-Poaching PII Masking**: Client portal displays masked candidate contact information.

---

## 6. Testing Strategy & Verification

The backend test suite (`backend/tests/test_hireai.py`) runs with `pytest` and verifies 11 core functional modules:
- Authentication & JWT issuance
- Role-based authorization gates
- Client organization data isolation
- SHA-256 and normalized contact duplicate detection
- Document parsing and text cleaning
- Mocked Groq JD structured extraction
- Deterministic candidate scoring & grade distribution
- Verbatim CV evidence generation
- Client shortlisting and mandatory rejection validation
- 11-stage pipeline status transitions
- DPDP Act Right-to-Erasure workflow

---

## 7. Assumptions & Limitations

1. **OCR Environment**: Tesseract OCR requires the host operating system to have `tesseract-ocr` installed. A graceful fallback is implemented when OCR binaries are unavailable.
2. **Groq Model Availability**: Default model is `llama-3.3-70b-versatile` with automatic fallback to high-fidelity deterministic rule-based extraction when API keys are unconfigured or offline.
3. **File Size Limit**: Configured to 25MB per CV file and 500 files per upload batch to prevent memory exhaustion.

