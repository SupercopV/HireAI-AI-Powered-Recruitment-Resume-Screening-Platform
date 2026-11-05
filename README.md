# HireAI – Intelligent Recruitment & Candidate Shortlisting Platform

> **Tagline**: *Smarter Hiring. Faster Shortlists. Fairer Decisions.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-06B6D4?style=flat&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)]()

---

## 📌 Product Overview

**HireAI** is a production-grade SaaS platform built for staffing companies and recruitment agencies to eliminate manual screening fatigue. It transforms messy, multi-page resumes into structured, ranked talent pools with **deterministic, explainable candidate scoring** and verifiable evidence quotations extracted directly from the original CV text.

The platform provides dedicated, role-isolated portals for **Recruiters** and **Client Hiring Managers**, complete with contact masking, India's DPDP Act 2023 compliance principles, and an 11-stage recruitment pipeline.

---

## ✨ Key Features & Capabilities

1. **Role-Based Access Control (RBAC)**:
   - **Recruiter**: Requisition management, AI scorecard extraction, bulk resume upload, deterministic candidate ranking, pipeline transitions, and DPDP compliance tools.
   - **Client Hiring Manager**: Isolated portal to review submitted profiles with masked contact info (no phone/email leakage), shortlist, reject with a mandatory reason, and propose interview dates.

2. **AI Job Scorecard Extraction (Groq API)**:
   - Ingests raw job descriptions and calls Groq (`llama-3.3-70b-versatile`) to extract must-have skills, secondary skills, experience ranges, notice limits, and CTC budget.
   - Human-in-the-loop review ensures recruiters can adjust criteria and customize weights before approving.

3. **High-Throughput Bulk Resume Ingestion (Up to 500 CVs)**:
   - Supports **PDF** (PyMuPDF) and **DOCX** (`python-docx`).
   - Automated **OCR fallback** with Tesseract for scanned image PDFs.
   - Instant **duplicate detection** using SHA-256 file hashing combined with normalized contact info (email and phone).

4. **Deterministic & Explainable Scoring Engine**:
   - Python-calculated arithmetic score (0–100):
     - Required Must-Have Skills (40 pts)
     - Total Experience Match (25 pts)
     - Relevant Domain Experience (15 pts)
     - Good-to-Have Secondary Skills (10 pts)
     - Notice Period Availability (10 pts)
   - **Strict Fairness Guarantee**: Candidate name, gender, age, photograph, marital status, and personal characteristics are 100% excluded from evaluation.
   - **Verbatim Evidence Quotes**: Quotes the exact supporting sentence from the CV text; explicitly displays *"Evidence not found"* if absent (never generates fake quotations).
   - **Zero Auto-Rejections**: Low-scoring candidates remain searchable.

5. **Client Portal & Data Privacy**:
   - Contact details masked (`r***@***.com`, `+91 ******910`) to prevent candidate poaching.
   - Mandatory client rejection reasons recorded in PostgreSQL.
   - Propose interview dates and times directly into the calendar.

6. **11-Stage Recruitment Lifecycle Kanban**:
   - Stages: *Sourced → Parsed → Screened → Shortlisted → Submitted to Client → Client Approved → Interview Scheduled → Interviewed → Offered → Joined → Rejected*.
   - Activity history timeline and audit trail.

7. **DPDP Act 2023 Compliance**:
   - Consent timestamping and purpose limitation logging.
   - Right-to-Erasure automated scrub: anonymizes PII and permanently purges CV files from storage.
   - Immutable security audit logs recording profile views.

---

## 🛠 Technology Stack

- **Frontend**: React 19, Vite, Tailwind CSS v4, React Router, Axios, Recharts, Lucide React.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic.
- **Database**: PostgreSQL (16 normalized tables).
- **AI Service**: Groq API (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`).
- **Parsing**: PyMuPDF, python-docx, Pillow, pytesseract.
- **Security**: JWT (`python-jose`), `bcrypt` (12 rounds).
- **Deployment**: Docker, Docker Compose, Vercel (Frontend), Render (Backend).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL running locally or via Docker

### 2. Demo Credentials
| Role | Email | Password | Organization |
| :--- | :--- | :--- | :--- |
| **Recruiter** | `recruiter@hireai.com` | `password123` | Apex Staffing Solutions |
| **Client Manager** | `client.hiring@fintechcorp.com` | `password123` | FinTech Global Corp |

*(A 1-click demo switcher is built directly into the UI header.)*

### 3. Local Setup
```bash
# Clone the repository
git clone https://github.com/hireai-enterprise/hireai.git
cd hireai

# Backend Setup
python -m venv venv
.\venv\Scripts\activate       # Windows (or: source venv/bin/activate on Unix)
pip install -r backend/requirements.txt

# Run migrations & seed realistic candidates and CV files
cd backend
alembic upgrade head
python seed.py
cd ..

# Start FastAPI Backend
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000

# Start React Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** to access the application.  
API documentation is available at **`http://localhost:8000/docs`**.

---

## 🐳 Docker Compose Deployment

Run the complete multi-service stack with a single command:
```bash
cp .env.example .env
docker-compose up --build -d
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## 🧪 Automated Testing

Run the automated test suite covering authentication, RBAC, duplicate detection, parsing, scoring, and client workflows:
```bash
pytest backend/tests/test_hireai.py -v
```

---

## 📚 Documentation
- [Technical Design Document (TDD)](docs/TDD.md)
- [Deployment & Operations Guide](docs/deployment.md)

