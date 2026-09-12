# AI Career Navigator — Data Architecture

## Purpose

This document defines the research-oriented data architecture
for the AI Career Navigator project.

The system integrates multiple evidence sources:

1. Occupational knowledge
   - O*NET
   - ESCO
   - NSDC/NQR

2. Academic curriculum
   - University and college syllabi

3. Learning resources
   - GeeksforGeeks
   - KodeKloud
   - Official documentation

4. Professional certifications
   - AWS
   - Microsoft
   - Cisco
   - Red Hat
   - Oracle

5. Student-generated evidence
   - Skills
   - Assessments
   - Academic background
   - Career preferences
   - Projects

## Core Principle

The system uses a canonical skill layer to connect
occupational requirements, academic curriculum,
learning resources, certifications, and student skills.

Source data is preserved separately from normalized
master data.

Raw datasets must not be directly modified.

Data processing must be reproducible.

## Data Processing Pipeline

Raw Sources
    ↓
Source Registration
    ↓
Raw Data Preservation
    ↓
Data Cleaning
    ↓
Normalization
    ↓
Deduplication
    ↓
Canonical Skill Mapping
    ↓
Master Dataset
    ↓
PostgreSQL
    ↓
Recommendation Engine

## Source Categories

### Occupational Knowledge

- O*NET
- ESCO
- NSDC/NQR

### Academic Curriculum

- Universities
- Colleges
- Degree programs
- Semester syllabi

### Learning Resources

- GeeksforGeeks
- KodeKloud
- Official documentation

### Professional Certifications

- AWS
- Microsoft
- Cisco
- Red Hat
- Oracle

### Market Data

- National Career Service
- Other legally accessible job-market sources
