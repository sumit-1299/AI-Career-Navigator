# AI Career Navigator

A comprehensive, production-grade AI-powered career guidance, skill-gap analysis, and interactive pathway exploration platform. Evaluates student competencies against industry benchmark roles, models multi-branch elective specializations, simulates "What-If" skill acquisition scenarios, and orchestrates end-to-end learning journeys across modern IT domains.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-WSGI-499848?style=flat-square&logo=gunicorn&logoColor=white)](https://gunicorn.org/)
[![Nginx](https://img.shields.io/badge/Nginx-1.25-009639?style=flat-square&logo=nginx&logoColor=white)](https://nginx.org/)

---

## 📌 Project Overview

**AI Career Navigator** addresses the gap between academic curricula and evolving technology industry demands. By structuring career roles, skill taxonomy, proficiency benchmarks, and student profiles into a normalized relational model, the system provides deterministic, explainable career readiness intelligence.

The platform provides a complete single-page application (SPA), interactive career decision visualizations, deterministic resume skill extraction, and production-ready WSGI / Nginx deployment support.

---

## 🏛️ System Architecture

```
                                 +--------------------------------+
                                 |   Web Browser / API Client    |
                                 +---------------+----------------+
                                                 | HTTP (Port 80 / 5173)
                                                 v
                     +-------------------------------------------------------+
                     |                 Nginx / Static Host                   |
                     |  - Serves React + Vite Static SPA (Gzip, Caching)     |
                     |  - Handles Client-Side Route Fallbacks (try_files)    |
                     |  - Reverse-proxies /api requests to Backend           |
                     +---------------------------+---------------------------+
                                                 | Upstream: http://127.0.0.1:5000
                                                 v
                     +-------------------------------------------------------+
                     |                 Gunicorn WSGI Server                  |
                     |  - Multi-worker Process Management (gunicorn.conf.py) |
                     |  - Flask 3.1 RESTful Application Factory (app.py)     |
                     |  - Stateless JWT Authentication & IDOR Protection     |
                     |  - Health Monitoring Probes (/api/health)             |
                     +---------------------------+---------------------------+
                                                 | SQL Connection (Port 5432)
                                                 v
                     +-------------------------------------------------------+
                     |                 PostgreSQL Engine                     |
                     |  - 11 Normalized Relational Schema Tables             |
                     |  - Canonical Skill Taxonomy & Provenance Sources      |
                     +-------------------------------------------------------+
```

### 1. Backend Architecture
- **Framework:** Flask 3.1 application factory (`backend/app.py`).
- **ORM:** SQLAlchemy 2.0 / Flask-SQLAlchemy with psycopg2 driver.
- **Production Server:** Gunicorn WSGI (`backend/gunicorn.conf.py`, `backend/wsgi.py`) configured with sync workers, configurable timeouts, and graceful worker restarts.
- **Security & Authorization:** `Flask-JWT-Extended` bearer tokens with HMAC-SHA256 signing, CORS headers, and IDOR validation on analytics endpoints.
- **Containerization (Module 10.2):** Standalone `backend/Dockerfile` based on `python:3.14-slim`, executing as an unprivileged user (`appuser`, UID 1000).

### 2. Frontend Architecture
- **Framework:** React 18 single-page application bundled with Vite 5.4.
- **Routing:** React Router v6 with 10 top-level views: Dashboard, Careers, Skill Gap, Skills, Learning, Resume, Compare, Analytics, Profile, and Auth.
- **Styling & UI:** Tailwind CSS with Lucide React iconography.
- **Production Serving (Module 10.3):** Multi-stage `frontend/Dockerfile` compiling assets and serving via Nginx 1.25 Alpine with dynamic DNS resolution, gzip compression, security headers (`X-Frame-Options`, `X-Content-Type-Options`), and SPA route fallback (`try_files $uri $uri/ /index.html`).

### 3. Database Architecture (11 Relational Tables)
The system operates on an intact, normalized PostgreSQL schema:
1. `users`: Credentials, password hashes, and timestamps.
2. `student_profiles`: Education level, major, graduation year, GPA.
3. `careers`: 10 standardized IT career tracks and domain classifications.
4. `career_preferences`: Student target career associations.
5. `canonical_skills`: 30 standardized canonical skills.
6. `skill_aliases`: 32 aliases mapped to canonical skills.
7. `skills`: Student-acquired skills and proficiencies (Levels 1–5).
8. `career_skills`: 50 weighted career-to-skill requirement mappings.
9. `data_sources`: Source provenance records (O\*NET, ESCO, NSDC, Prototype).
10. `learning_resources`: Curated courses, tutorials, and certifications.
11. `user_learning_progress`: User learning module progress and completion tracking.

---

## ✨ Features Overview (Phases 1–10)

- **Standardized IT Knowledge Base:** 10 core tracks with 50+ weighted skill requirements.
- **Intelligent Skill Gap Engine:** Weighted readiness calculation distinguishing missing skills from proficiency deficits.
- **Resume Extraction Pipeline:** Deterministic resume parsing and skill identification.
- **Interactive Study Roadmaps:** Phased milestone sequencing and estimated study weeks calculation.
- **Student Learning Analytics:** Readiness velocity tracking and learning trajectory metrics.
- **Curated Learning Resources:** High-quality courses mapped to canonical skill gaps.
- **Dual Career Comparison (Module 9.2):** Salary differentials, market demand deltas, and transition difficulty ratings.
- **Elective Specialization Trees (Module 9.3):** Branching pathway trees identifying shared core vs. elective competencies.
- **"What-If I Learn Skill X?" Simulator (Module 9.4):** Deterministic, reversible hypothetical skill impact calculation.
- **Production Readiness & Hardening (Phase 10):** Standardized health probes (`/api/health`), WSGI server configuration, Nginx serving, deployment scripts, and operational documentation.

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` to configure your deployment:

```bash
cp .env.example .env
```

### Environment Variables Reference

| Variable | Default / Example | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://career_app:password@localhost:5432/career_navigator` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | `your-cryptographically-secure-key` | Secret key used to sign and verify JWT tokens |
| `FLASK_ENV` | `production` | Application environment mode (`production` / `development`) |
| `FLASK_DEBUG` | `False` | Enables/disables Flask debug mode |
| `CORS_ORIGINS` | `*` | Allowed origins for CORS headers (comma-separated or `*`) |
| `PORT` | `5000` | Port for the backend WSGI HTTP server |
| `GUNICORN_WORKERS` | `2` | Number of Gunicorn worker processes |
| `GUNICORN_TIMEOUT` | `60` | Gunicorn worker timeout in seconds |
| `VITE_API_URL` | `http://localhost:5000` | API upstream base URL for frontend builds |

> [!IMPORTANT]
> Never commit `.env` or production credentials to version control. The repository `.gitignore` ensures `.env` remains untracked.

---

## 🚀 Deployment & Operation Guide

### 1. Deployment Support Scripts (`scripts/`)

The repository includes shell scripts in `scripts/` using safe shell practices (`set -euo pipefail`):

| Script | Purpose |
| :--- | :--- |
| `scripts/deploy.sh` | Pre-deployment environment validation, frontend bundling, and health check. |
| `scripts/start_backend.sh` | Starts the backend using Gunicorn WSGI (`gunicorn.conf.py`) or Python. |
| `scripts/build_frontend.sh` | Executes Vite production build and verifies asset output in `frontend/dist`. |
| `scripts/health_check.sh` | Queries `/api/health` and verifies service and database status. |

Make scripts executable:
```bash
chmod +x scripts/*.sh
```

Execute deployment preparation:
```bash
./scripts/deploy.sh
```

---

### 2. Local Development Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start backend server
python app.py
```
Backend runs on [http://localhost:5000](http://localhost:5000).

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend development server runs on [http://localhost:5173](http://localhost:5173).

---

### 3. Production Serving Procedure

#### Starting the Backend
```bash
# Option A: Using the deployment startup script
./scripts/start_backend.sh

# Option B: Direct Gunicorn invocation
cd backend
gunicorn --config gunicorn.conf.py wsgi:app
```

#### Building the Frontend for Production
```bash
# Option A: Using the build script
./scripts/build_frontend.sh

# Option B: Direct npm invocation
npm --prefix frontend run build
```
Production assets are generated in `frontend/dist/`. Serve these assets using Nginx or your preferred web server with SPA route fallback enabled (`try_files $uri $uri/ /index.html`).

#### Standalone Container Builds (Phases 10.2 & 10.3)
```bash
# Build backend container
docker build -t ai-career-backend ./backend

# Build frontend container
docker build -t ai-career-frontend ./frontend
```

---

## 📡 API Reference Catalog

### Core & Health Monitoring
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/` | API status message | No |
| `GET` | `/api/health` | Standardized health check probe (`status`, `database`, `environment`) | No |

### Authentication
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/register` | Register a new user account | No |
| `POST` | `/api/login` | Authenticate user and issue JWT bearer token | No |

### Student Profile & Skills
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/profile` | Retrieve student academic profile | Yes (JWT) |
| `POST` | `/api/profile` | Create or update student profile | Yes (JWT) |
| `GET` | `/api/skills` | List user's assessed skills | Yes (JWT) |
| `POST` | `/api/skills` | Add or update a user skill | Yes (JWT) |
| `POST` | `/api/resume/extract-skills` | Extract skills from uploaded resume | Yes (JWT) |

### Career Intelligence & Recommendations
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/careers` | List all 10 standardized IT career tracks | No |
| `GET` | `/api/careers/<id>` | Retrieve career details and required skill matrix | No |
| `GET` | `/api/careers/recommendations` | Ranked career readiness recommendations | Optional JWT |
| `GET` | `/api/careers/<id>/skill-gap` | Detailed skill gap assessment for target career | Optional JWT |
| `GET` | `/api/careers/<id>/roadmap` | Structured learning roadmap and timeline estimation | Optional JWT |
| `GET` | `/api/careers/<id>/analytics` | Student readiness velocity and learning trajectory | Yes (JWT) |

### Transition Pathways & Simulation (Phase 9)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/careers/compare` | Dual career comparison with salary & demand deltas | Optional JWT |
| `GET` | `/api/careers/<from>/transition/<to>` | Career transition difficulty & transferable skills | Optional JWT |
| `GET` | `/api/careers/<id>/pathways` | Interactive elective specialization pathway tree | Optional JWT |
| `POST` | `/api/careers/<id>/simulate-skill` | Deterministic "What-If" skill acquisition simulator | Optional JWT |

### Learning Resources (Phase 8)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/learning-resources` | Curated learning resources catalog | No |
| `GET` | `/api/learning-resources/progress` | User learning progress and module completion | Optional JWT |
| `POST` | `/api/learning-resources/<id>/progress`| Update user progress on learning resource | Optional JWT |

---

## 🔍 Health Checks & Logging

### Health Check Verification
Run the automated health probe:
```bash
./scripts/health_check.sh http://127.0.0.1:5000/api/health
```

Expected JSON response:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production",
  "service": "ai-career-navigator"
}
```

### Logging Expectations
- **Gunicorn WSGI:** Access and error logs are streamed to standard output/standard error (`accesslog = "-"` and `errorlog = "-"` in `backend/gunicorn.conf.py`).
- **Nginx:** Access logs are written to `/var/log/nginx/access.log` and error logs to `/var/log/nginx/error.log`.
- **Database Handshake:** Backend logs verify connectivity to PostgreSQL before binding to incoming traffic.

---

## 🛠️ Troubleshooting Common Deployment Problems

1. **Database Connection Refused (`psycopg2.OperationalError`):**
   - Verify PostgreSQL server is running: `sudo systemctl status postgresql` or verify host port `5432`.
   - Verify credentials in `.env` match database user permissions.
2. **CORS Errors in Browser:**
   - Ensure `CORS_ORIGINS` in `.env` includes the frontend origin (e.g., `http://localhost:5173` or your production domain).
3. **Single Page Application 404 on Refresh:**
   - Ensure the web server (Nginx) has SPA fallback configured: `try_files $uri $uri/ /index.html;`.
4. **JWT Expiration / 401 Unauthorized:**
   - Verify tokens are passed in the header: `Authorization: Bearer <token>`.
   - JWT default expiration is 24 hours. Re-authenticate via `/api/login` if expired.

---

## 🔄 Rollback & Git Release Procedure

The project adheres to a strict linear Git checkpoint policy:
1. **Inspecting Commits:** `git log --oneline -5`
2. **Safe Rollback Policy:** Always prefer `git revert <commit-hash>` to record rollback actions explicitly rather than rewriting public history.
3. **Working Tree Verification:** Before and after any release or rollback, ensure `git status` reports a clean working tree.
4. **Pushing Releases:** Push verified commits to `origin/main` without force pushing (`git push origin main`).

---

## 🧪 Testing & Quality Assurance

### 1. Full Backend Regression Suite (162 Tests)
```bash
PYTHONPATH=backend backend/venv/bin/python -m unittest discover -s backend/tests
```
Executes all regression suites covering Phases 1 through 9 (157 tests) and Phase 10.1 (5 tests).

### 2. Frontend Production Build Check
```bash
./scripts/build_frontend.sh
```

---

## 📂 Repository Structure

```
AI-Career-Navigator/
├── backend/
│   ├── app.py                       # Flask application factory, health probe & CORS
│   ├── config.py                    # Environment configuration classes
│   ├── extensions.py                # Database and JWT extensions
│   ├── gunicorn.conf.py             # Production Gunicorn WSGI configuration
│   ├── wsgi.py                      # WSGI entry point
│   ├── Dockerfile                   # Python 3.14-slim production container
│   ├── requirements.txt             # Python dependencies
│   ├── models/                      # SQLAlchemy models (11 relational tables)
│   ├── routes/                      # Modular API blueprints
│   ├── services/                    # Core business logic services
│   └── tests/                       # Complete regression test suite (162 tests)
├── frontend/
│   ├── src/
│   │   ├── components/              # Reusable React UI components
│   │   ├── pages/                   # Single-Page Application route views
│   │   ├── services/                # Axios/Fetch API client bindings
│   │   ├── App.jsx                  # React Router configuration
│   │   └── main.jsx                 # React root mount
│   ├── nginx.conf                   # Nginx reverse proxy and SPA routing
│   ├── Dockerfile                   # Multi-stage Node/Nginx container
│   └── package.json                 # Frontend dependencies
├── scripts/
│   ├── deploy.sh                    # Deployment preparation & verification script
│   ├── start_backend.sh             # Backend production startup script
│   ├── build_frontend.sh            # Frontend production build script
│   └── health_check.sh              # Backend health check probe script
├── docs/
│   ├── PROJECT_STATUS.md            # Comprehensive phase completion tracking
│   └── PROJECT_SCOPE.md             # Original project scope document
├── .env.example                     # Environment template
├── .gitignore                       # Version control ignore rules
└── README.md                        # Complete project documentation
```

---

## 📄 License

This project is maintained for educational, technical demonstration, and portfolio purposes.
