# Deployment and Operations Guide – HireAI

HireAI is designed for modern cloud deployment:
- **Frontend**: Vercel
- **Backend**: Render
- **Database**: Render PostgreSQL / Supabase / Neon / AWS RDS

---

## 1. Demo Login Credentials

For quick evaluation and demonstrations, the application is pre-seeded with two standard accounts:

| Role | Email | Password | Organization | Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Recruiter** | `recruiter@hireai.com` | `password123` | Apex Staffing Solutions | Full access to Requisitions, Scorecards, Bulk CV Upload, AI Shortlists, Pipeline Kanban, Privacy & Audit Trail. |
| **Client Hiring Manager** | `client.hiring@fintechcorp.com` | `password123` | FinTech Global Corp | Isolated view of submitted candidates with masked PII, Shortlist, Reject with mandatory reason, Propose Interviews. |

*Tip: A one-click demo role switcher button is available in the top navigation bar for immediate perspective switching.*

---

## 2. Environment Variables Specification

### Backend Environment Variables (`.env`)

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Application stage | `production` or `development` |
| `PORT` | HTTP port | `8000` |
| `HOST` | Bind address | `0.0.0.0` |
| `SECRET_KEY` | JWT encryption secret key (32+ chars) | `openssl rand -hex 32` |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Bearer token validity in minutes | `1440` (24 hours) |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `GROQ_API_KEY` | Groq Cloud API key | `gsk_...` |
| `GROQ_MODEL` | Groq supported LLM model | `llama-3.3-70b-versatile` |
| `MAX_UPLOAD_SIZE_MB` | Maximum allowed CV file size | `25` |
| `MAX_CV_BATCH_SIZE` | Maximum CVs per upload batch | `500` |
| `UPLOAD_DIR` | Local disk upload directory | `./uploads` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:5173,https://your-hireai.vercel.app` |

### Frontend Environment Variables (`frontend/.env`)

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Base API URL pointing to FastAPI backend | `http://localhost:8000/api` or `https://hireai-api.onrender.com/api` |

---

## 3. Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 14+ (or Docker)

### Step 1: Clone and Set Up Backend
```bash
# In the root repository directory
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 2: Configure Database & Run Migrations
```bash
# Ensure PostgreSQL database 'hireai' exists, then set DATABASE_URL in .env:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/hireai

# Run Alembic migrations to create tables
cd backend
alembic upgrade head
cd ..

# Seed the database with realistic sample candidates and CV files
python backend/seed.py
```

### Step 3: Run Backend Server
```bash
# From project root
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
# API Docs available at http://localhost:8000/docs
```

### Step 4: Run Frontend Server
```bash
cd frontend
npm install
npm run dev
# Accessible at http://localhost:5173
```

---

## 4. Docker Compose Setup (Single Command)

To run the full stack (PostgreSQL, FastAPI Backend, React Frontend) in isolated Docker containers:

```bash
# Copy and configure environment variables
cp .env.example .env

# Build and start all services
docker-compose up --build -d

# Check service health
docker-compose ps

# Access Frontend at http://localhost:5173
# Access Backend API at http://localhost:8000/docs
```

---

## 5. Cloud Production Deployment

### A. Database Deployment (Neon Serverless PostgreSQL Recommended)

Neon ([neon.tech](https://neon.tech)) is an ideal cloud database provider for HireAI because of its generous free tier, automatic scale-to-zero when idle, and built-in connection pooling:

1. **Sign up**: Go to [neon.tech](https://neon.tech) and create a free account (no credit card required).
2. **Create a Project**: Click **New Project**, name it `hireai`, and select a region closest to your backend (e.g. `US East (Ohio)` or `Frankfurt`).
3. **Copy Connection String**: From the Neon Dashboard, copy the connection string. Neon provides:
   - **Pooled connection string** (recommended for production API):
     `postgresql://<user>:<password>@<ep-xyz-pooler>.<region>.aws.neon.tech/hireai?sslmode=require`
4. **Configure in HireAI**: Set this connection string in your backend `.env` or Render environment variables:
   ```env
   DATABASE_URL=postgresql://<user>:<password>@<ep-xyz-pooler>.<region>.aws.neon.tech/hireai?sslmode=require
   ```
5. **Run Migrations & Seed Data**:
   ```bash
   # Apply all 16 tables via Alembic
   alembic upgrade head

   # Seed initial demo accounts and requisitions
   python backend/seed.py
   ```
   *(Note: HireAI's SQLAlchemy engine is already pre-configured with `pool_pre_ping=True` and Alembic uses `NullPool`, ensuring flawless reconnection when Neon auto-resumes from suspension).*

### B. Backend Deployment on Render
1. In Render Dashboard, click **New +** → **Web Service**.
2. Connect your Git repository.
3. Select **Root Directory**: `backend` (or root with Dockerfile).
4. Environment: **Docker** or **Python 3**.
   - If Python:
     - Build Command: `pip install -r requirements.txt && alembic upgrade head && python seed.py`
     - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   - `DATABASE_URL`: Your hosted PostgreSQL URL.
   - `SECRET_KEY`: Secure random string.
   - `GROQ_API_KEY`: Your Groq API key.
   - `GROQ_MODEL`: `llama-3.3-70b-versatile`.
   - `CORS_ORIGINS`: Your Vercel frontend URL.
6. Deploy the service. Note the backend URL (e.g. `https://hireai-api.onrender.com`).

### C. Frontend Deployment on Vercel
1. In Vercel Dashboard, click **Add New Project**.
2. Import your Git repository.
3. Set **Root Directory** to `frontend`.
4. Framework Preset: **Vite**.
5. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://hireai-api.onrender.com/api`
6. Click **Deploy**. Your frontend is live with automatic SSL!

---

## 6. Running Automated Tests

```bash
# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Execute pytest suite with verbose output
pytest backend/tests/test_hireai.py -v
```

