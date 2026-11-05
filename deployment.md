# HireAI – Comprehensive Deployment & Operations Guide

> **Project**: HireAI – Intelligent Recruitment & Candidate Shortlisting Platform  
> **Repository**: [https://github.com/SupercopV/HireAI-AI-Powered-Recruitment-Resume-Screening-Platform](https://github.com/SupercopV/HireAI-AI-Powered-Recruitment-Resume-Screening-Platform)  
> **Target Environment**: Local Development, Docker Containers, and Cloud Staging (Render / Neon / Vercel)  
> **Live URL Status**: Not deployed (Local development & evaluation environment)

---

## 1. Project Prerequisites & Software Requirements

Before deploying HireAI, ensure the host machine meets the following software prerequisites:

| Software | Minimum Version | Recommended Version | Verification Command | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | `3.11.0` | `3.13+` | `python --version` | FastAPI backend runtime, scoring engine, parsers |
| **Node.js** | `18.0.0` | `20.x` or `22.x` | `node -v` | React 19 / Vite frontend build runtime |
| **npm** | `9.0.0` | `10.x+` | `npm -v` | Frontend dependency package manager |
| **Git** | `2.30.0` | Latest | `git --version` | Version control and repository management |
| **PostgreSQL** | `14.0` | `16` or `18` | `psql --version` | Primary relational database (or Docker / Neon) |
| **Docker** | `24.0.0` | Latest *(Optional)* | `docker --version` | Containerized 1-command local deployment |
| **Tesseract OCR** | `4.0.0` | `5.0+` *(Optional)* | `tesseract --version` | OCR fallback for scanned/image-only PDF resumes |

---

## 2. GitHub Repository Cloning

Clone the official repository to your local workspace:

```bash
# Clone the repository
git clone https://github.com/SupercopV/HireAI-AI-Powered-Recruitment-Resume-Screening-Platform.git

# Navigate into the project root directory
cd HireAI-AI-Powered-Recruitment-Resume-Screening-Platform
```

---

## 3. Backend Virtual Environment Setup & Dependencies

HireAI's backend is built with FastAPI and requires Python dependencies managed inside an isolated virtual environment.

### Step 3.1: Create & Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
# Create virtual environment named 'venv'
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux (Bash or Zsh):**
```bash
# Create virtual environment named 'venv'
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Step 3.2: Install Backend Dependencies

With the virtual environment active, install the pinned production requirements:

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

> [!NOTE]
> The dependencies include `fastapi`, `uvicorn`, `sqlalchemy>=2.0`, `alembic`, `pydantic>=2.0`, `psycopg[binary]`, `python-jose[cryptography]`, `passlib[bcrypt]`, `bcrypt==4.0.1`, `pymupdf`, `python-docx`, `openpyxl`, `pytesseract`, `httpx`, and `groq`.

---

## 4. Database Configuration (Local PostgreSQL & Neon Cloud)

HireAI supports both local PostgreSQL installations and serverless cloud databases like **Neon**.

### Option A: Local PostgreSQL Setup (Standard Port 5432 or 5433)

1. Open your terminal or `psql` shell and create the database:
   ```sql
   CREATE DATABASE hireai;
   ```
2. Verify user permissions:
   ```sql
   -- Ensure the user has full access
   GRANT ALL PRIVILEGES ON DATABASE hireai TO postgres;
   ```
3. Set your connection string in your `.env` file:
   ```env
   DATABASE_URL=postgresql://postgres:<YOUR_LOCAL_PASSWORD>@localhost:5432/hireai
   ```
   *(If your local PostgreSQL is running on an alternate port, such as `5433`, update the port accordingly: `@localhost:5433/hireai`)*

---

### Option B: Neon Serverless PostgreSQL Configuration

HireAI has native support for [Neon](https://neon.tech) serverless PostgreSQL:

1. **Sign Up / Log In**: Navigate to [https://neon.tech](https://neon.tech) and create a free project.
2. **Create Project**: Name the project `hireai` and select your nearest geographic region.
3. **Obtain Connection String**: From the Neon Dashboard, copy the **Pooled connection string**. It follows this structure:
   ```text
   postgresql://<NEON_USER>:<NEON_PASSWORD>@<EP_IDENTIFIER>-pooler.<REGION>.aws.neon.tech/hireai?sslmode=require
   ```
4. **Set in `.env`**: Set `DATABASE_URL` in your backend `.env` file:
   ```env
   DATABASE_URL=postgresql://<NEON_USER>:<NEON_PASSWORD>@<EP_IDENTIFIER>-pooler.<REGION>.aws.neon.tech/hireai?sslmode=require
   ```
5. **Architectural Compatibility**: HireAI's database engine is pre-configured with `pool_pre_ping=True` and Alembic uses `NullPool`, ensuring instant and resilient reconnections when Neon serverless clusters resume from sleep mode.

---

## 5. Environment Variables Specification

Create a `.env` file in the project root directory by copying the provided `.env.example`:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

### Complete Environment Variable Reference:

| Environment Variable | Required | Default / Example Value | Description |
| :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | Yes | `development` or `production` | Application execution environment. |
| `PORT` | Yes | `8000` | HTTP port on which the FastAPI server listens. |
| `HOST` | Yes | `0.0.0.0` | Bind address (`0.0.0.0` for all interfaces). |
| `SECRET_KEY` | Yes | `<SECURE_RANDOM_32_CHAR_STRING>` | Cryptographic secret used for signing JWT tokens. |
| `ALGORITHM` | Yes | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | `1440` | JWT bearer token validity window (1440 mins = 24 hrs). |
| `DATABASE_URL` | Yes | `postgresql://<USER>:<PASS>@<HOST>:<PORT>/hireai` | PostgreSQL connection URI. |
| `GROQ_API_KEY` | No* | `<YOUR_GROQ_API_KEY>` | Groq Cloud API key (`gsk_...`). *System has automated offline fallback. |
| `GROQ_MODEL` | Yes | `llama-3.3-70b-versatile` | Supported Groq model for JD extraction and candidate analysis. |
| `MAX_UPLOAD_SIZE_MB` | Yes | `25` | Maximum allowed individual CV file upload size in megabytes. |
| `MAX_CV_BATCH_SIZE` | Yes | `500` | Maximum count of CV files / rows allowed per upload batch. |
| `UPLOAD_DIR` | Yes | `./uploads` | Local disk vault directory for parsed candidate documents. |
| `CORS_ORIGINS` | Yes | `http://localhost:5173,http://localhost:3000` | Comma-separated list of allowed frontend origin URLs. |

### Frontend Environment Variable (`frontend/.env`):

| Environment Variable | Required | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000/api` | Base HTTP endpoint URL pointing to the FastAPI backend. |

> [!CAUTION]
> Never commit actual passwords, API keys, JWT secrets, or production database credentials to version control. Keep `.env` strictly within `.gitignore`.

---

## 6. Groq AI Service Configuration

HireAI leverages the Groq Cloud API for sub-second LLM inference using **`llama-3.3-70b-versatile`**.

1. Obtain a free API key from [https://console.groq.com/keys](https://console.groq.com/keys).
2. Set the key in your `.env` file:
   ```env
   GROQ_API_KEY=gsk_yourGroqApiKeyHere
   GROQ_MODEL=llama-3.3-70b-versatile
   ```
3. **Automated Offline Fallback**: If `GROQ_API_KEY` is omitted, expired, or rate-limited, HireAI automatically falls back to an embedded deterministic rule-based extractor. The application will continue functioning without throwing unhandled exceptions.

---

## 7. Database Migrations & Data Seeding

HireAI uses Alembic for declarative database versioning and includes a comprehensive seed script that populates realistic organizations, requisitions, candidates, and synthetic CV files.

### Step 7.1: Apply Alembic Schema Migrations

Run all database migrations from the project root:

```bash
cd backend
alembic upgrade head
cd ..
```
*This command executes revision `bde8b4f10c03_initial_hireai_schema.py` and creates all 16 normalized tables.*

### Step 7.2: Seed the Database with Realistic Sample Data

Execute the seed script:

```bash
python backend/seed.py
```

**What the seed script provisions:**
- **2 Organizations**: *Apex Staffing Solutions* (Agency) and *FinTech Global Corp* (Client).
- **2 Demo Accounts**: Recruiter account and Client Hiring Manager account.
- **2 Active Requisitions**: Senior Full-Stack Engineer and Lead Data Scientist.
- **2 Approved Scorecards**: Pre-configured with technical criteria, experience bounds, and category weights.
- **16 Synthetic Resumes**: Generated `.pdf` and `.docx` candidate CV files in `sample_data/cvs/`.
- **16 Candidate Profiles**: Pre-screened candidates with deterministic scores (0–100) and verbatim CV evidence quotations.
- **Client Submissions & Feedback**: Active submissions, feedback notes, and proposed interview dates.

---

## 8. Starting the Application Servers

### Step 8.1: Start FastAPI Backend Server

In your first terminal (with the virtual environment activated):

```bash
# From project root directory
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger API Documentation**: `http://localhost:8000/docs`
- **Health Check Endpoint**: `http://localhost:8000/health`

---

### Step 8.2: Start React / Vite Frontend Server

In your second terminal:

```bash
# Navigate to frontend folder
cd frontend

# Install Node dependencies (first time only)
npm install

# Start Vite development server
npm run dev
```
- **Frontend Web Application**: `http://localhost:5173`

---

## 9. Pre-Configured Demo Login Credentials

For quick evaluation and role-switching demonstrations, use the pre-seeded credentials:

| Role | Email Address | Password | Organization | Portal Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Recruiter** | `recruiter@hireai.com` | `password123` | Apex Staffing Solutions | Requisition management, AI JD scorecard extraction, bulk resume upload (PDF/DOCX/XLSX), candidate ranking, verbatim evidence drawer, pipeline Kanban, DPDP privacy management, and audit logs. |
| **Client Hiring Manager** | `client.hiring@fintechcorp.com` | `password123` | FinTech Global Corp | Isolated view of candidates submitted specifically to FinTech Corp; masked candidate contact details (anti-poaching); shortlist candidates; reject with mandatory reason; propose interview dates/times. |

*Tip: A 1-click demo credential switcher is integrated directly into the login screen and the top navigation bar.*

---

## 10. Running the Automated Test Suite

HireAI includes a comprehensive automated test suite covering authentication, RBAC boundaries, duplicate detection, parsing, deterministic scoring, client review actions, and privacy workflows.

With your virtual environment active, run pytest from the project root:

```bash
pytest backend/tests/test_hireai.py -v
```

### Verified Test Suite Results (13 Tests):
```text
backend/tests/test_hireai.py::test_login_success PASSED                  [  7%]
backend/tests/test_hireai.py::test_login_invalid_credentials PASSED      [ 15%]
backend/tests/test_hireai.py::test_recruiter_can_access_requisitions PASSED [ 23%]
backend/tests/test_hireai.py::test_client_cannot_create_requisition PASSED [ 30%]
backend/tests/test_hireai.py::test_duplicate_detection_by_hash_and_email PASSED [ 38%]
backend/tests/test_hireai.py::test_resume_parser_docx_and_cleaning PASSED [ 46%]
backend/tests/test_hireai.py::test_jd_analysis_mocked PASSED             [ 53%]
backend/tests/test_hireai.py::test_deterministic_scoring_fairness_and_evidence PASSED [ 61%]
backend/tests/test_hireai.py::test_client_shortlist_and_rejection PASSED [ 69%]
backend/tests/test_pipeline_transition PASSED                            [ 76%]
backend/tests/test_candidate_deletion_request PASSED                     [ 84%]
backend/tests/test_excel_template_download PASSED                        [ 92%]
backend/tests/test_excel_bulk_upload PASSED                              [100%]

======================== 13 passed in 3.10s ========================
```

---

## 11. Alternative: 1-Command Docker Compose Deployment

If you have Docker and Docker Compose installed, you can launch the complete 3-tier architecture (PostgreSQL, FastAPI Backend, React Frontend) with one command:

```bash
# 1. Copy sample environment file
cp .env.example .env

# 2. Build and start containers in the background
docker-compose up --build -d
```

- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **Stop Containers**: `docker-compose down`

---

## 12. Troubleshooting & Common Issues

### Issue 1: Database Connection Refused (`connection to server at "localhost", port 5432 failed`)
- **Cause**: Local PostgreSQL service is stopped or running on a non-standard port.
- **Solution**:
  - Verify PostgreSQL service status in Windows Services or run `Get-Service -Name *postgres*`.
  - Check your configured port in `postgresql.conf` (e.g. `5433` vs `5432`) and update `DATABASE_URL` in `.env`.

### Issue 2: `ModuleNotFoundError: No module named 'psycopg'`
- **Cause**: SQLAlchemy 2.0+ default postgres dialect expects `psycopg` (v3).
- **Solution**: Run `pip install "psycopg[binary]"` inside your active virtual environment.

### Issue 3: `ImportError: email-validator is not installed`
- **Cause**: Pydantic's `EmailStr` field validation requires `email-validator`.
- **Solution**: Run `pip install email-validator` inside your virtual environment.

### Issue 4: `pytesseract.TesseractNotFoundError` on Scanned Resumes
- **Cause**: Tesseract OCR engine binary is not installed on the system PATH.
- **Solution**:
  - Windows: Download installer from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add `C:\Program Files\Tesseract-OCR` to system PATH.
  - Linux/Ubuntu: `sudo apt-get install -y tesseract-ocr`.
  - *Note: Text-based PDFs and DOCX resumes do not require Tesseract and parse instantly via PyMuPDF.*

### Issue 5: CORS Errors in Browser Console
- **Cause**: Frontend origin URL is missing from `CORS_ORIGINS`.
- **Solution**: Ensure your frontend URL (e.g. `http://localhost:5173`) is listed in `CORS_ORIGINS` in `.env`.

---

## 13. Security and Production Checklist

When moving HireAI from local evaluation to a hosted cloud production environment:

1. **Rotate Secret Key**: Generate a cryptographically secure 64-character secret using `python -c "import secrets; print(secrets.token_hex(32))"`.
2. **Enforce SSL/TLS**: Ensure `DATABASE_URL` includes `?sslmode=require` when connecting to hosted databases.
3. **Set CORS Origins**: Restrict `CORS_ORIGINS` strictly to your production domain (e.g. `https://your-hireai.vercel.app`).
4. **Configure S3 Storage**: For enterprise-scale production, transition `UPLOAD_DIR` to an AWS S3 / Cloudflare R2 bucket with pre-signed upload URLs.

