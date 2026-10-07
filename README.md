# AI Career Navigator

A personalized career guidance and skill-gap mapping RESTful API that evaluates student profiles, analyzes industry career requirements, and models structured pathways across modern IT domains.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![JWT](https://img.shields.io/badge/JWT-Authentication-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)](https://jwt.io/)

---

## 📌 Project Overview

**AI Career Navigator** is a backend service designed to address the disconnect between academic curricula and industry skill demands. By structuring career roles, core skills, proficiency weights, and student profiles into an interconnected relational model, the system enables systematic identification of skill gaps and facilitates personalized career navigation.

---

## 🎯 Problem Statement

Students and early-career developers frequently encounter difficulties identifying the exact technical competencies required for specific IT specializations (such as DevOps, Cloud Engineering, or Data Science). Academic qualifications alone rarely provide a clear roadmap of required proficiency levels. **AI Career Navigator** formalizes this process through:
1. Standardized IT career definitions and domain categorization.
2. Weighted career-skill mappings with defined minimum proficiency thresholds.
3. Student profile tracking and preferred career pathway management.

---

## ✨ Features

- **JWT Authentication & Authorization**: Secure user registration and login with token-based session handling via `Flask-JWT-Extended`.
- **Student Profile Management**: Structured data models tracking academic background, education level, graduation year, and GPA.
- **Career Knowledge Base**:
  - 10 structured IT career tracks (Software Developer, Web Developer, Data Analyst, Data Scientist, AI/ML Engineer, Cloud Engineer, DevOps Engineer, Cybersecurity Analyst, Network Engineer, Database Administrator).
  - 50+ weighted career-to-skill relationships specifying importance levels and required proficiencies.
- **Automated Data Ingestion**: Duplicate-safe CSV ingestion pipeline for loading and updating standardized career and skill datasets (`data/careers.csv`, `data/career_skills.csv`).
- **Relational Data Modeling**: Fully normalized relational schema implemented using SQLAlchemy 2.0 and PostgreSQL.
- **Modular Blueprint Architecture**: Clean separation of concerns with isolated blueprints for authentication, profile management, skills, and career preferences.

---

## 🏛️ System Architecture

```
                      +-----------------------------+
                      |       Client / Postman      |
                      +--------------+--------------+
                                     | HTTP / JSON (JWT)
                                     v
                      +-----------------------------+
                      |        Flask 3.1 App        |
                      +--------------+--------------+
                                     |
         +-----------------+---------+---------+-----------------+
         |                 |                   |                 |
         v                 v                   v                 v
   +-----------+     +-----------+       +-----------+     +-------------------+
   |  Auth BP  |     | Profile BP|       | Skills BP |     | Career Prefs BP   |
   +-----+-----+     +-----+-----+       +-----+-----+     +---------+---------+
         |                 |                   |                     |
         +-----------------+---------+---------+---------------------+
                                     |
                                     v
                      +-----------------------------+
                      |     SQLAlchemy 2.0 ORM      |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |     PostgreSQL Database     |
                      |  (Users, Profiles, Careers, |
                      |    Skills, CareerSkills)    |
                      +-----------------------------+
```

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core programming language |
| **Framework** | Flask 3.1 | Lightweight WSGI web application framework |
| **ORM** | Flask-SQLAlchemy / SQLAlchemy 2.0 | Object-relational mapping and database abstraction |
| **Database** | PostgreSQL | Robust relational database for normalized career data |
| **Authentication** | Flask-JWT-Extended, PyJWT | Stateless JSON Web Token authentication |
| **Migrations** | Flask-Migrate / Alembic | Database schema versioning and migrations |
| **Environment** | python-dotenv | Environment variable configuration management |

---

## 📂 Repository Structure

```
AI-Career-Navigator/
├── backend/
│   ├── app.py                     # Flask application factory and entry point
│   ├── config.py                  # Environment-driven configuration
│   ├── extensions.py              # Initialized extensions (SQLAlchemy)
│   ├── models/
│   │   ├── user.py                # User account model
│   │   ├── student_profile.py     # Student academic profile model
│   │   ├── career.py              # Career track model
│   │   ├── skill.py               # Skill definition model
│   │   ├── career_skill.py        # Weighted career-skill association model
│   │   └── career_preference.py   # Student career preference model
│   ├── routes/
│   │   ├── auth.py                # Registration and login endpoints
│   │   ├── profile.py             # Student profile CRUD
│   │   ├── skills.py              # Skill management endpoints
│   │   └── career_preferences.py  # Career preference tracking endpoints
│   ├── scripts/                   # Data import and candidate build scripts
│   ├── requirements.txt           # Python package dependencies
│   └── .env.example               # Template environment file
├── data/
│   ├── careers.csv                # Standardized career dataset
│   └── career_skills.csv          # Career-to-skill mapping dataset
├── docs/
│   ├── PROJECT_SCOPE.md           # Scope documentation
│   └── PROJECT_STATUS.md          # Implementation progress tracking
└── README.md
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10 or higher
- PostgreSQL server installed and running
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/sumit-1299/AI-Career-Navigator.git
cd AI-Career-Navigator/backend
```

### 2. Create and Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables Configuration

Copy the example environment file and configure your PostgreSQL database credentials and JWT secret key:

```bash
cp .env.example .env
```

Edit `.env` with your local settings:

```ini
DATABASE_URL=postgresql://username:password@localhost:5432/career_navigator_db
JWT_SECRET_KEY=your_secure_jwt_secret_key_here
```

### 5. Initialize Database & Seed Career Data

Ensure your PostgreSQL database exists, then run the database initialization and seed scripts:

```bash
# Verify database connection
python app.py
```

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/` | API status health check | No |
| `GET` | `/db-test` | Database connectivity verification | No |
| `POST` | `/api/auth/register` | Register a new user account | No |
| `POST` | `/api/auth/login` | Authenticate user and return JWT | No |
| `GET` | `/api/profile` | Retrieve student profile | Yes (JWT) |
| `POST` | `/api/profile` | Create/update student profile | Yes (JWT) |
| `GET` | `/api/skills` | List available skills | No |
| `POST` | `/api/career-preferences` | Save student career preferences | Yes (JWT) |

---

## 🔮 Future Improvements

- **Frontend Interface**: React-based dashboard for interactive roadmap visualization.
- **Automated Skill Gap Scoring**: Algorithmic assessment scoring comparing current student competencies against target role requirements.
- **Course & Certification Recommendations**: Integration with external learning resources mapped to identified skill gaps.
- **Docker Containerization**: Multi-container `docker-compose.yml` for simplified deployment with PostgreSQL.

---

## 📄 License

This project is maintained for educational and portfolio demonstration purposes.

