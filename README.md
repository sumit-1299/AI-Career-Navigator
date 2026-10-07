# AI Career Navigator

A comprehensive, production-grade AI-powered career guidance, skill-gap analysis, and interactive pathway exploration platform. Evaluates student competencies against industry benchmark roles, models multi-branch elective specializations, simulates "What-If" skill acquisition scenarios, and orchestrates end-to-end learning journeys across modern IT domains.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Nginx](https://img.shields.io/badge/Nginx-1.25-009639?style=flat-square&logo=nginx&logoColor=white)](https://nginx.org/)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-WSGI-499848?style=flat-square&logo=gunicorn&logoColor=white)](https://gunicorn.org/)

---

## 📌 Project Overview

**AI Career Navigator** bridges the gap between academic curricula and real-world technology industry demands. By structuring career roles, skill taxonomy, proficiency benchmarks, and student profiles into a normalized relational model, the system provides deterministic, explainable career readiness intelligence.

The platform offers a full-stack, containerized experience with single-page application (SPA) routing, interactive career decision visualizations, deterministic resume skill extraction, and production-ready multi-container orchestration.

---

## 🏛️ System Architecture

```
                                 +--------------------------------+
                                 |   Web Browser / API Client    |
                                 +---------------+----------------+
                                                 | HTTP (Port 80)
                                                 v
                     +-------------------------------------------------------+
                     |                 Nginx Reverse Proxy                   |
                     |      (Frontend Container: ai_career_frontend)         |
                     |  - Serves React + Vite Static SPA (Gzip, Caching)     |
                     |  - Handles Client-Side Route Fallbacks                |
                     |  - Reverse-proxies /api requests to Backend           |
                     +---------------------------+---------------------------+
                                                 | Upstream: http://backend:5000
                                                 v
                     +-------------------------------------------------------+
                     |                 Gunicorn WSGI Server                  |
                     |       (Backend Container: ai_career_backend)          |
                     |  - Multi-worker Process Management                    |
                     |  - Flask 3.1 RESTful Application Factory              |
                     |  - JWT Stateless Authentication & IDOR Protection     |
                     |  - Automated Startup Database TCP Handshake           |
                     +---------------------------+---------------------------+
                                                 | SQL: postgres:5432
                                                 v
                     +-------------------------------------------------------+
                     |                 PostgreSQL 16 Engine                  |
                     |      (Database Container: ai_career_postgres)         |
                     |  - 11 Normalized Relational Schema Tables             |
                     |  - Persistent Named Volume: ai_career_postgres_data   |
                     |  - Initialized with Reference Catalog (init.sql)      |
                     +-------------------------------------------------------+
```

---

## ✨ Key Features Across Phases 1–10

### 1. Standardized IT Career Knowledge Base
- **10 Core IT Tracks:** Software Developer, Web Developer, Data Analyst, Data Scientist, AI/ML Engineer, Cloud Engineer, DevOps Engineer, Cybersecurity Analyst, Network Engineer, Database Administrator.
- **50+ Weighted Skill Mappings:** Granular importance weighting and minimum required proficiency benchmarks (Levels 1–5).
- **Taxonomy Normalization:** Canonical skill mappings integrated with O\*NET, ESCO, and NSDC data source provenance.

### 2. Intelligent Skill Gap Engine & Recommendations
- **Algorithmic Readiness Scoring:** Weighted percentage calculation comparing student skills against career requirements.
- **Identified Gaps & Deficits:** Differentiates missing skills (proficiency = 0) from proficiency deficits (current < required).
- **Ranked Career Recommendations:** Suggests best-fit career tracks sorted by immediate readiness score.

### 3. Resume Skill Extraction Pipeline
- Automated resume parsing with deterministic keyword matching and regex normalization.
- Discovers acquired skills and infers candidate confidence levels without modifying user data unless explicitly confirmed.

### 4. Interactive Study Roadmaps & Timeline Planning
- **Phased Milestone Progression:** Structures learning into Foundation, Core, and Advanced phases.
- **Estimated Study Weeks Calculator:** Deterministic timeline estimation parameterized by student study hours per week.
- **Curated Learning Resources:** High-quality courses, tutorials, and certifications linked directly to missing skills.

### 5. Multi-Career Transition Pathway Explorer
- Side-by-side comparative analysis between any two careers.
- Calculates salary differentials, market demand deltas, study week differences, and overall transition difficulty rating (Low, Medium, High).
- O\*NET-aligned transferable skills analysis.

### 6. Interactive Elective Specialization Tree (Module 9.3)
- Models multiple valid specialization pathways toward a target career.
- Distinguishes **Core Competencies** from **Elective Specialization Branches**.
- Computes student match scores for each branch and identifies shared vs. unique branch competencies.

### 7. "What-If I Learn Skill X?" Career Simulator (Module 9.4)
- Deterministic, explainable, and reversible hypothetical career readiness simulator.
- Allows students to simulate acquiring or upgrading any skill to evaluate the exact impact on career readiness **without permanently modifying their real profile**.

### 8. Production Hardening & Health Monitoring (Phase 10)
- **Monitoring Health Probe:** Standardized `GET /api/health` checking service state and live database connectivity.
- **WSGI Production Packaging:** Gunicorn process management with non-root security (`appuser`).
- **Nginx Reverse Proxy:** Dynamic DNS resolution (`127.0.0.11`), security headers, and SPA routing fallback.
- **Docker Compose Orchestration:** Complete multi-container deployment with persistent database storage.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend Framework** | React 18 | Declarative single-page application |
| **Build Tool** | Vite 5.4 | Ultra-fast build and bundling tool |
| **Styling & Icons** | Tailwind CSS, Lucide React | Modern utility styling and iconography |
| **Web Server / Proxy** | Nginx 1.25 Alpine | Reverse proxy, static asset server, SPA fallback |
| **Backend Framework** | Flask 3.1 | Modular RESTful API backend |
| **WSGI Server** | Gunicorn 23.0 | Production Python WSGI HTTP server |
| **Database ORM** | Flask-SQLAlchemy / SQLAlchemy 2.0 | Object-relational mapping and database abstraction |
| **Database** | PostgreSQL 16 Alpine | Robust relational database storage |
| **Authentication** | Flask-JWT-Extended | Stateless JSON Web Token authentication |
| **Orchestration** | Docker Compose | Multi-container deployment specification |

---

## 🚀 Quick Start with Docker Compose (Recommended)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (v24.0+)
- [Docker Compose](https://docs.docker.com/compose/) (v2.20+)

### 1. Clone & Configure
```bash
git clone https://github.com/sumit-1299/AI-Career-Navigator.git
cd AI-Career-Navigator

# Copy example environment configuration
cp .env.example .env
```

### 2. Launch the Stack
```bash
docker compose up -d
```

Docker Compose builds the images and starts all services in the correct dependency order:
1. `ai_career_postgres` initializes and loads catalog data from `database/init.sql`.
2. `ai_career_backend` verifies database connectivity and boots Gunicorn.
3. `ai_career_frontend` starts Nginx, serving the React UI and reverse proxying `/api`.

### 3. Verify Health & Running Services
```bash
docker compose ps
```

All 3 containers should report `healthy` or `Up`:
- **Frontend Web UI:** [http://localhost](http://localhost) (Port 80)
- **Backend API Direct:** [http://localhost:5001](http://localhost:5001) (Port 5001)
- **PostgreSQL Database:** `localhost:5434` (Port 5434)
- **Health Check Probe:** [http://localhost/api/health](http://localhost/api/health)

### 4. Run Automated Deployment Smoke Tests
```bash
python scripts/production_smoke_test.py --url http://localhost
```
Runs 25 automated assertions verifying frontend routing, API health, authentication, career pathways, simulator, and boundary security.

### 5. Stop the Stack
```bash
# Stop containers (preserves database data)
docker compose down

# Stop containers and remove persistent volume
docker compose down -v
```

---

## 💻 Local Development Setup

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start backend server
python app.py
```
Backend runs locally on [http://localhost:5000](http://localhost:5000).

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend development server runs on [http://localhost:5173](http://localhost:5173).

---

## 📡 API Reference Catalog

### Core & Health
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/` | API status message | Public |
| `GET` | `/api/health` | Service and database health monitoring probe | Public |

### Authentication
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/register` | Register a new user account | Public |
| `POST` | `/api/login` | Authenticate user and issue JWT bearer token | Public |

### Student Profile & Skills
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/profile` | Retrieve student academic profile | JWT |
| `POST` | `/api/profile` | Create or update student profile | JWT |
| `GET` | `/api/skills` | List user's assessed skills | JWT |
| `POST` | `/api/skills` | Add or update a user skill | JWT |
| `POST` | `/api/resume/extract-skills` | Extract skills from uploaded resume | JWT |

### Career Intelligence & Recommendations
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/careers` | List all 10 standardized IT career tracks | Public |
| `GET` | `/api/careers/<id>` | Retrieve career details and required skill matrix | Public |
| `GET` | `/api/careers/recommendations` | Ranked career readiness recommendations | Optional JWT |
| `GET` | `/api/careers/<id>/skill-gap` | Detailed skill gap assessment for target career | Optional JWT |
| `GET` | `/api/careers/<id>/roadmap` | Structured learning roadmap and timeline estimation | Optional JWT |
| `GET` | `/api/careers/<id>/analytics` | Student readiness velocity and learning trajectory | JWT |

### Transition Pathways & Simulation (Phase 9)
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/careers/compare` | Dual career comparison with salary & demand deltas | Optional JWT |
| `GET` | `/api/careers/<from>/transition/<to>` | Career transition difficulty & transferable skills | Optional JWT |
| `GET` | `/api/careers/<id>/pathways` | Interactive elective specialization pathway tree | Optional JWT |
| `POST` | `/api/careers/<id>/simulate-skill` | Deterministic "What-If" skill acquisition simulator | Optional JWT |

### Learning Resources (Phase 8)
| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/learning-resources` | Curated learning resources catalog | Public |
| `GET` | `/api/learning-resources/progress` | User learning progress and module completion | Optional JWT |
| `POST` | `/api/learning-resources/<id>/progress`| Update user progress on learning resource | Optional JWT |

---

## 🧪 Testing & Quality Assurance

### 1. Full Backend Regression Suite (162 Tests)
```bash
PYTHONPATH=backend backend/venv/bin/python -m unittest discover -s backend/tests
```
Executes the complete regression test suite covering all phases (Phases 1 through 10).

### 2. Frontend Production Build Check
```bash
npm --prefix frontend run build
```
Validates Vite compilation, JSX syntax, and asset bundling with 0 errors.

### 3. Production Deployment Smoke Test
```bash
python scripts/production_smoke_test.py --url http://localhost
```
Validates the live multi-container environment end-to-end.

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
│   ├── entrypoint.sh                # Container database handshake startup script
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
├── database/
│   └── init.sql                     # PostgreSQL schema DDL and reference seed data
├── scripts/
│   └── production_smoke_test.py     # Automated deployment verification suite
├── docs/
│   ├── PROJECT_STATUS.md            # Comprehensive phase completion tracking
│   └── PROJECT_SCOPE.md             # Original project scope document
├── docker-compose.yml               # Multi-container orchestration definition
├── .env.example                     # Environment template
├── .dockerignore                    # Build ignore rules
├── .gitignore                       # Version control ignore rules
└── README.md                        # Project documentation
```

---

## 📄 License

This project is maintained for educational, technical demonstration, and portfolio purposes.
