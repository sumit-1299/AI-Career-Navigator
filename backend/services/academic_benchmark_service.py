"""
Academic Recommendation Benchmarking Engine for AI Career Navigator.
Phase 11 Module 11.3: Academic Recommendation Benchmarking.

Evaluates:
ACADEMIC CURRICULUM EVIDENCE -> TARGET CAREER REQUIREMENTS -> STUDENT PROFICIENCY

Three Critical Separate Concepts:
1. ACADEMIC COVERAGE:
   Whether the curriculum contains evidence that this skill/topic is taught.
   (Does NOT mean the student is professionally proficient in this skill).
2. STUDENT PROFICIENCY:
   The student's actual demonstrated proficiency level recorded in their profile.
3. CAREER REQUIREMENT:
   The competency level and importance required by the target IT career track.

DATA PROVENANCE & TRANSPARENCY:
All sample/demo degree programs are explicitly labeled:
"DEMO / SAMPLE / PROTOTYPE — NOT OFFICIAL UNIVERSITY CURRICULUM DATA".
No fake university claims or unauthorized external downloads are made.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from models.student_profile import StudentProfile
from models.canonical_skill import CanonicalSkill
from models.skill_alias import SkillAlias
from services.skill_gap_service import SkillGapService, SkillGapStatus
from services.skill_roi_service import SkillRoiService
from services.portfolio_project_service import PortfolioProjectService
from utils.normalization import normalize_skill_name, strip_parenthetical_qualifiers


# ==============================================================================
# SAMPLE / DEMO ACADEMIC CURRICULUM CATALOG
# ==============================================================================
# PROVENANCE NOTICE:
# DEMO / SAMPLE / PROTOTYPE — NOT OFFICIAL UNIVERSITY CURRICULUM DATA.
# Provides standardized benchmark baselines reflecting typical undergraduate
# course syllabi for computer science and IT degrees.
# ==============================================================================

PROVENANCE_NOTICE = (
    "DEMO / SAMPLE / PROTOTYPE — NOT OFFICIAL UNIVERSITY CURRICULUM DATA. "
    "Benchmarked against typical standardized coursework topics."
)

SAMPLE_ACADEMIC_CURRICULA: Dict[str, Dict[str, Any]] = {
    "btech_cs": {
        "program_id": "btech_cs",
        "program_name": "B.Tech Computer Science & Engineering (Sample Baseline)",
        "degree_level": "Undergraduate (4-Year)",
        "provenance": PROVENANCE_NOTICE,
        "description": "Standard university undergraduate CS syllabus covering foundational algorithms, data structures, systems, and databases.",
        "courses": [
            {
                "course_code": "CS101",
                "course_name": "Computer Programming & Problem Solving",
                "semester": 1,
                "skills_evidenced": ["Python", "C++"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CS201",
                "course_name": "Data Structures & Algorithm Analysis",
                "semester": 3,
                "skills_evidenced": ["Data Structures"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CS202",
                "course_name": "Object-Oriented Software Design with Java",
                "semester": 3,
                "skills_evidenced": ["Java"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CS301",
                "course_name": "Database Management Systems & Relational Theory",
                "semester": 4,
                "skills_evidenced": ["SQL"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CS302",
                "course_name": "Operating Systems & Unix Architecture",
                "semester": 4,
                "skills_evidenced": ["Linux"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CS303",
                "course_name": "Computer Networks & Protocol Stacks",
                "semester": 5,
                "skills_evidenced": ["Networking"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CS304",
                "course_name": "Software Engineering & Version Control",
                "semester": 5,
                "skills_evidenced": ["Git"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CS401",
                "course_name": "Introduction to Artificial Intelligence & Machine Learning",
                "semester": 6,
                "skills_evidenced": ["Machine Learning", "Statistics"],
                "coverage_strength": 0.8,
                "evidence_type": "Department Elective"
            },
            {
                "course_code": "CS402",
                "course_name": "Internet Technologies & Client-Side Scripting",
                "semester": 6,
                "skills_evidenced": ["HTML", "CSS", "JavaScript"],
                "coverage_strength": 0.8,
                "evidence_type": "Department Elective"
            }
        ]
    },
    "bca_mca": {
        "program_id": "bca_mca",
        "program_name": "BCA / MCA Computer Applications (Sample Baseline)",
        "degree_level": "Undergraduate / Postgraduate Applied",
        "provenance": PROVENANCE_NOTICE,
        "description": "Applied computing syllabus emphasizing web technologies, application development, and database administration.",
        "courses": [
            {
                "course_code": "CA101",
                "course_name": "Core Java Programming & OOP Paradigms",
                "semester": 1,
                "skills_evidenced": ["Java"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CA102",
                "course_name": "Web Technologies & Interactive UI Development",
                "semester": 2,
                "skills_evidenced": ["HTML", "CSS", "JavaScript"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CA201",
                "course_name": "Relational Database Management Systems & MySQL",
                "semester": 3,
                "skills_evidenced": ["SQL", "MySQL"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CA202",
                "course_name": "Python Programming & Data Structures",
                "semester": 3,
                "skills_evidenced": ["Python", "Data Structures"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CA301",
                "course_name": "Modern Frontend Frameworks & Single-Page Apps",
                "semester": 4,
                "skills_evidenced": ["React", "JavaScript"],
                "coverage_strength": 0.8,
                "evidence_type": "Elective Course"
            },
            {
                "course_code": "CA302",
                "course_name": "Network Administration & Linux Essentials",
                "semester": 4,
                "skills_evidenced": ["Networking", "Linux"],
                "coverage_strength": 0.8,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "CA401",
                "course_name": "Database Security & Enterprise Storage",
                "semester": 5,
                "skills_evidenced": ["Database Security", "PostgreSQL"],
                "coverage_strength": 0.8,
                "evidence_type": "Elective Course"
            }
        ]
    },
    "bsc_data_science": {
        "program_id": "bsc_data_science",
        "program_name": "B.Sc / M.Sc Data Science & AI (Sample Baseline)",
        "degree_level": "Specialized Applied Science",
        "provenance": PROVENANCE_NOTICE,
        "description": "Specialized curriculum focusing on statistical modeling, mathematical foundations, Python data stack, and machine learning.",
        "courses": [
            {
                "course_code": "DS101",
                "course_name": "Python for Scientific Computing & Data Analysis",
                "semester": 1,
                "skills_evidenced": ["Python", "Pandas"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "DS102",
                "course_name": "Probability & Applied Statistics",
                "semester": 1,
                "skills_evidenced": ["Statistics", "Excel"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "DS201",
                "course_name": "SQL & Relational Databases for Analytics",
                "semester": 2,
                "skills_evidenced": ["SQL"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "DS202",
                "course_name": "Linear Algebra & Computational Structures",
                "semester": 2,
                "skills_evidenced": ["Data Structures"],
                "coverage_strength": 0.8,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "DS301",
                "course_name": "Supervised & Unsupervised Machine Learning",
                "semester": 3,
                "skills_evidenced": ["Machine Learning", "Python"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "DS302",
                "course_name": "Deep Learning & Neural Networks",
                "semester": 4,
                "skills_evidenced": ["Deep Learning", "TensorFlow"],
                "coverage_strength": 0.8,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "DS401",
                "course_name": "Business Intelligence & Interactive Dashboarding",
                "semester": 4,
                "skills_evidenced": ["Power BI", "Excel"],
                "coverage_strength": 0.8,
                "evidence_type": "Elective Course"
            }
        ]
    },
    "btech_it": {
        "program_id": "btech_it",
        "program_name": "B.Tech Information Technology & Infrastructure (Sample Baseline)",
        "degree_level": "Undergraduate (4-Year)",
        "provenance": PROVENANCE_NOTICE,
        "description": "IT infrastructure, systems administration, and network security engineering curriculum.",
        "courses": [
            {
                "course_code": "IT101",
                "course_name": "Scripting Languages & Python Programming",
                "semester": 1,
                "skills_evidenced": ["Python"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "IT201",
                "course_name": "Computer Networks & Routing Architecture",
                "semester": 3,
                "skills_evidenced": ["Networking", "Routing and Switching"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "IT202",
                "course_name": "Linux Systems Administration & Shell",
                "semester": 3,
                "skills_evidenced": ["Linux"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "IT301",
                "course_name": "Network Security & Cryptography",
                "semester": 4,
                "skills_evidenced": ["Network Security", "Cybersecurity"],
                "coverage_strength": 1.0,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "IT302",
                "course_name": "Database Management & Security",
                "semester": 4,
                "skills_evidenced": ["SQL", "Database Security"],
                "coverage_strength": 0.8,
                "evidence_type": "Core Course"
            },
            {
                "course_code": "IT401",
                "course_name": "Software Engineering & Version Control",
                "semester": 5,
                "skills_evidenced": ["Git"],
                "coverage_strength": 0.8,
                "evidence_type": "Core Course"
            }
        ]
    }
}


class AcademicBenchmarkService:
    """
    Core engine for Academic Recommendation Benchmarking.
    Computes deterministic, explainable alignment between academic curricula,
    career requirements, and student demonstrated proficiencies.
    """

    @classmethod
    def get_sample_programs(cls) -> List[Dict[str, Any]]:
        """Returns metadata for all available sample academic curriculum baselines."""
        return [
            {
                "program_id": prog["program_id"],
                "program_name": prog["program_name"],
                "degree_level": prog["degree_level"],
                "provenance": prog["provenance"],
                "description": prog["description"],
                "course_count": len(prog["courses"])
            }
            for prog in SAMPLE_ACADEMIC_CURRICULA.values()
        ]

    @classmethod
    def detect_student_program(
        cls,
        user_id: Optional[int] = None,
        requested_program: Optional[str] = None
    ) -> str:
        """
        Determines the appropriate academic curriculum ID.
        Uses explicit request if valid, otherwise inspects StudentProfile if available,
        defaulting to 'btech_cs'.
        """
        if requested_program and requested_program in SAMPLE_ACADEMIC_CURRICULA:
            return requested_program

        if user_id:
            try:
                profile = StudentProfile.query.filter_by(user_id=user_id).first()
                if profile:
                    ed_text = f"{profile.education or ''} {profile.specialization or ''}".lower()
                    if "data science" in ed_text or "analytics" in ed_text or "ai" in ed_text:
                        return "bsc_data_science"
                    if "mca" in ed_text or "bca" in ed_text or "application" in ed_text:
                        return "bca_mca"
                    if "it" in ed_text or "information technology" in ed_text:
                        return "btech_it"
            except Exception:
                pass

        return "btech_cs"

    @classmethod
    def extract_academic_skills(
        cls,
        curriculum: Dict[str, Any],
        custom_evidence: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extracts all academic skills evidenced in the curriculum or custom evidence.
        Maps each normalized skill name to its coverage strength and evidenced courses.
        """
        academic_map: Dict[str, Dict[str, Any]] = {}

        courses = list(curriculum.get("courses", []))
        if custom_evidence:
            courses.extend(custom_evidence)

        for course in courses:
            code = course.get("course_code")
            name = course.get("course_name") or course.get("course") or "Academic Course"
            c_name = f"{code}: {name}" if code and not name.startswith(code) else name
            strength = float(course.get("coverage_strength", 1.0))
            skills_list = course.get("skills_evidenced") or course.get("skills") or []
            if isinstance(skills_list, str):
                skills_list = [skills_list]

            for s in skills_list:
                norm_s = normalize_skill_name(s)
                if not norm_s:
                    continue

                if norm_s not in academic_map:
                    academic_map[norm_s] = {
                        "skill_name": s,
                        "canonical_name": s,
                        "coverage_strength": strength,
                        "courses": [c_name]
                    }
                else:
                    academic_map[norm_s]["coverage_strength"] = max(
                        academic_map[norm_s]["coverage_strength"],
                        strength
                    )
                    if c_name not in academic_map[norm_s]["courses"]:
                        academic_map[norm_s]["courses"].append(c_name)

                # Also map stripped taxonomic qualifiers
                stripped = normalize_skill_name(strip_parenthetical_qualifiers(s))
                if stripped and stripped not in academic_map:
                    academic_map[stripped] = academic_map[norm_s]

        return academic_map

    @classmethod
    def resolve_academic_match(
        cls,
        career_skill_name: str,
        academic_map: Dict[str, Dict[str, Any]]
    ) -> Tuple[bool, float, List[str]]:
        """
        Resolves whether a career skill is evidenced in academic curriculum.
        Accounts for canonical aliases, case-insensitivity, and taxonomy qualifiers.
        """
        norm_name = normalize_skill_name(career_skill_name)
        stripped = normalize_skill_name(strip_parenthetical_qualifiers(career_skill_name))

        # 1. Direct match
        if norm_name in academic_map:
            entry = academic_map[norm_name]
            return True, entry["coverage_strength"], entry["courses"]

        if stripped in academic_map:
            entry = academic_map[stripped]
            return True, entry["coverage_strength"], entry["courses"]

        # 2. Match via database SkillAlias if available
        try:
            alias_rec = SkillAlias.query.filter_by(normalized_alias=norm_name).first()
            if alias_rec and alias_rec.canonical_skill:
                c_norm = normalize_skill_name(alias_rec.canonical_skill.canonical_name)
                if c_norm in academic_map:
                    entry = academic_map[c_norm]
                    return True, entry["coverage_strength"], entry["courses"]
        except Exception:
            pass

        return False, 0.0, []

    @classmethod
    def calculate_academic_alignment_score(
        cls,
        breakdown: List[Dict[str, Any]]
    ) -> float:
        """
        Computes the deterministic, importance-weighted Academic-to-Career Alignment Score.
        Formula:
            Score = (sum(importance * coverage_strength) / sum(importance)) * 100
        """
        if not breakdown:
            return 0.0

        total_weight = sum(item.get("importance", 1) for item in breakdown)
        if total_weight <= 0:
            return 0.0

        covered_weight = sum(
            item.get("importance", 1) * float(item.get("coverage_strength", 0.0))
            for item in breakdown
        )

        score = (covered_weight / float(total_weight)) * 100.0
        return round(max(0.0, min(100.0, score)), 1)

    @classmethod
    def benchmark_career_curriculum(
        cls,
        career_id: int,
        user_id: Optional[int] = None,
        program_id: Optional[str] = None,
        custom_curriculum: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes the full Academic Recommendation Benchmarking analysis for a career track.
        Compares curriculum evidence against career requirements and student proficiency.
        """
        career = Career.query.get(career_id)
        if not career:
            return {
                "error": "CAREER_NOT_FOUND",
                "message": f"Career with ID {career_id} not found"
            }

        career_skills: List[CareerSkill] = (
            career.skills if hasattr(career, "skills") and career.skills else
            CareerSkill.query.filter_by(career_id=career.id).all()
        )

        # 1. Select Program
        active_prog_id = cls.detect_student_program(user_id=user_id, requested_program=program_id)
        program = SAMPLE_ACADEMIC_CURRICULA.get(active_prog_id, SAMPLE_ACADEMIC_CURRICULA["btech_cs"])

        # 2. Extract Academic Evidenced Skills
        academic_map = cls.extract_academic_skills(program, custom_evidence=custom_curriculum)

        # 3. Retrieve Student Skills & Readiness (if user_id provided)
        is_personalized = False
        student_skills_map: Dict[str, Skill] = {}
        student_readiness_score = 0.0

        if user_id:
            is_personalized = True
            student_skills = Skill.query.filter_by(user_id=user_id).all()
            for s in student_skills:
                student_skills_map[normalize_skill_name(s.skill_name)] = s

            try:
                gap_eval = SkillGapService.evaluate_career_gap(career, student_skills)
                student_readiness_score = gap_eval["summary"]["readiness_percentage"]
            except Exception:
                student_readiness_score = 0.0

        # 4. Integrate Phase 11.1 Skill ROI ranking (if applicable)
        roi_lookup: Dict[str, Dict[str, Any]] = {}
        try:
            roi_res = SkillRoiService.rank_career_skill_rois(career.id, user_id=user_id)
            for r in roi_res.get("ranked_skills", []):
                roi_lookup[normalize_skill_name(r["skill_name"])] = r
        except Exception:
            pass

        # 5. Evaluate Career Skills against Academic Coverage & Student Proficiency
        breakdown: List[Dict[str, Any]] = []
        academic_foundations: List[str] = []
        industry_gaps: List[str] = []
        student_gaps: List[str] = []
        priority_actions: List[Dict[str, Any]] = []

        for cs in career_skills:
            cs_name = cs.skill_name
            cs_importance = cs.importance or 1
            cs_required = cs.required_level or 3

            # Academic Coverage check
            is_covered, strength, courses = cls.resolve_academic_match(cs_name, academic_map)
            coverage_label = "COVERED" if is_covered else "NOT_COVERED"

            # Student Proficiency check
            norm_cs = normalize_skill_name(cs_name)
            student_skill = student_skills_map.get(norm_cs)
            raw_prof = student_skill.proficiency if student_skill else 0
            norm_curr = round(raw_prof / 2.0, 2)
            gap_val = max(0.0, round(cs_required - norm_curr, 2))

            if not student_skill:
                student_status = SkillGapStatus.MISSING
            elif gap_val > 0:
                student_status = SkillGapStatus.WEAK
            else:
                student_status = SkillGapStatus.MATCHED

            # Categorize into the 4 Analytical Benchmark States
            if is_covered and student_status in [SkillGapStatus.MATCHED, SkillGapStatus.EXCEEDS]:
                benchmark_status = "ACADEMICALLY_ANCHORED_AND_SATISFIED"
                status_label = "Academically Covered & Proficient"
                action_text = "Core academic foundation verified and demonstrated."
            elif is_covered:
                benchmark_status = "ACADEMIC_FOUNDATION_NEEDS_REINFORCEMENT"
                status_label = "Taught in Curriculum (Needs Practical Reinforcement)"
                action_text = f"Reinforce hands-on implementation from {cs_required}/5 required level."
            elif student_status in [SkillGapStatus.MATCHED, SkillGapStatus.EXCEEDS]:
                benchmark_status = "SELF_TAUGHT_INDUSTRY_ADVANTAGE"
                status_label = "Self-Taught Industry Skill (Beyond Academic Syllabus)"
                action_text = "Demonstrated competitive strength beyond academic curriculum."
            else:
                benchmark_status = "INDUSTRY_GAP_ACTION_REQUIRED"
                status_label = "Industry-Specific Gap (Not Evidenced in Academic Syllabus)"
                action_text = "Acquire through specialized projects, tooling labs, or industry certifications."

            if is_covered:
                academic_foundations.append(cs_name)
            else:
                industry_gaps.append(cs_name)

            if student_status in [SkillGapStatus.MISSING, SkillGapStatus.WEAK]:
                student_gaps.append(cs_name)

            # Enrich with Module 11.1 Skill ROI data if available
            roi_info = roi_lookup.get(norm_cs, {})
            is_qw = roi_info.get("is_quickest_win", False)
            readiness_gain = roi_info.get("readiness_gain", round(cs_importance * 2.5, 1))
            roi_score = roi_info.get("roi_score", round(readiness_gain / 2.0, 1))

            item_data = {
                "skill_name": cs_name,
                "importance": cs_importance,
                "required_level": cs_required,
                "academic_coverage": coverage_label,
                "coverage_strength": strength,
                "courses_evidenced": courses,
                "student_proficiency": norm_curr,
                "raw_proficiency": raw_prof,
                "student_status": student_status,
                "gap_value": gap_val,
                "benchmark_status": benchmark_status,
                "status_label": status_label,
                "readiness_gain": readiness_gain,
                "roi_score": roi_score,
                "is_quickest_win": is_qw
            }
            breakdown.append(item_data)

            # Build Priority Actions for unfulfilled competencies
            if benchmark_status in ["INDUSTRY_GAP_ACTION_REQUIRED", "ACADEMIC_FOUNDATION_NEEDS_REINFORCEMENT"]:
                priority_actions.append({
                    "skill_name": cs_name,
                    "importance": cs_importance,
                    "type": "INDUSTRY_GAP" if not is_covered else "ACADEMIC_REINFORCEMENT",
                    "benchmark_status": benchmark_status,
                    "status_label": status_label,
                    "action": action_text,
                    "readiness_gain": readiness_gain,
                    "roi_score": roi_score,
                    "is_quickest_win": is_qw,
                    "courses_evidenced": courses
                })

        # Sort Priority Actions deterministically: Quickest Win first, then highest ROI, then importance
        priority_actions.sort(
            key=lambda x: (
                -int(x["is_quickest_win"]),
                -x["roi_score"],
                -x["importance"],
                x["skill_name"]
            )
        )

        # 6. Calculate Academic-to-Career Alignment Score
        alignment_score = cls.calculate_academic_alignment_score(breakdown)

        # 7. Integrate Phase 11.2 Capstone Bridge
        recommended_capstone = None
        try:
            portfolio_res = PortfolioProjectService.recommend_projects_for_career(
                career_id=career.id,
                user_id=user_id,
                limit=3
            )
            # Find the best project that specifically bridges industry gaps
            cand_projects = portfolio_res.get("recommendations", [])
            for p in cand_projects:
                missing_addressed = set(p.get("missing_skills_addressed", []))
                if any(ig in missing_addressed for ig in industry_gaps):
                    recommended_capstone = {
                        "project_id": p["project_id"],
                        "title": p["title"],
                        "difficulty": p["difficulty"],
                        "estimated_hours": p["estimated_hours"],
                        "bridges_industry_gaps": list(set(industry_gaps).intersection(missing_addressed)),
                        "recommendation_reason": p.get("recommendation_reason", "")
                    }
                    break
            if not recommended_capstone and cand_projects:
                p = cand_projects[0]
                recommended_capstone = {
                    "project_id": p["project_id"],
                    "title": p["title"],
                    "difficulty": p["difficulty"],
                    "estimated_hours": p["estimated_hours"],
                    "bridges_industry_gaps": [],
                    "recommendation_reason": p.get("recommendation_reason", "")
                }
        except Exception:
            pass

        # 8. Generate Natural-Language Explainable Benchmark Summary
        summary_parts = [
            f"Your academic curriculum ({program['program_name']}) provides foundational coursework "
            f"for {len(academic_foundations)} of {len(career_skills)} required competencies "
            f"({alignment_score}% Academic-to-Career Alignment)."
        ]
        if industry_gaps:
            summary_parts.append(
                f"However, industry-specific technologies ({', '.join(industry_gaps)}) are not "
                f"typically covered in standard undergraduate coursework and must be bridged via self-directed projects."
            )
        if is_personalized and student_gaps:
            summary_parts.append(
                f"In your individual profile, {len(student_gaps)} competencies remain below target level, "
                f"including academic areas that require practical hands-on reinforcement."
            )
        elif is_personalized:
            summary_parts.append(
                "Your individual profile currently satisfies the foundational competencies for this career track."
            )

        benchmark_summary = " ".join(summary_parts)

        return {
            "career_id": career.id,
            "career_title": career.title,
            "domain": career.domain,
            "program_id": program["program_id"],
            "program_name": program["program_name"],
            "degree_level": program["degree_level"],
            "provenance_notice": PROVENANCE_NOTICE,
            "is_personalized": is_personalized,
            "academic_alignment_score": alignment_score,
            "student_readiness_score": student_readiness_score,
            "total_career_skills_count": len(career_skills),
            "academic_covered_count": len(academic_foundations),
            "academic_gap_count": len(industry_gaps),
            "student_gap_count": len(student_gaps),
            "academic_foundations": academic_foundations,
            "industry_gaps": industry_gaps,
            "student_gaps": student_gaps,
            "curriculum_breakdown": breakdown,
            "priority_actions": priority_actions,
            "recommended_capstone_project": recommended_capstone,
            "benchmark_summary": benchmark_summary,
            "available_programs": cls.get_sample_programs()
        }
