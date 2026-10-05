"""
Resume Skill Extraction Foundation for AI Career Navigator.

Provides end-to-end ingestion and extraction pipeline:
Resume Upload (PDF / DOCX / TXT) -> File Validation -> Text Extraction ->
Section Segmentation -> Skill Detection -> Normalization -> Canonical Skill Mapping ->
Confidence Scoring & Review Flagging -> Student Skill Profile.
"""

import io
import os
import re
import xml.etree.ElementTree as ET
import zipfile
import zlib
from typing import Any, Dict, List, Optional, Set, Tuple

from extensions import db
from models.canonical_skill import CanonicalSkill
from models.skill import Skill
from models.skill_alias import SkillAlias
from utils.normalization import normalize_skill_name


MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10 MB limit

SECTION_PATTERNS = {
    "skills": re.compile(
        r"(?i)\b(skills|technical skills|technologies|proficiencies|tools & technologies|core competencies)\b"
    ),
    "experience": re.compile(
        r"(?i)\b(experience|work experience|professional experience|employment history|work history)\b"
    ),
    "projects": re.compile(
        r"(?i)\b(projects|technical projects|academic projects|key projects)\b"
    ),
    "certifications": re.compile(
        r"(?i)\b(certifications|licenses & certifications|credentials|accreditations)\b"
    ),
    "education": re.compile(
        r"(?i)\b(education|academic background|qualifications)\b"
    ),
}


class ResumeExtractionService:
    """Service for validating, parsing, and extracting canonical skills from resumes."""

    # -------------------------------------------------------------
    # FILE VALIDATION & TEXT EXTRACTION (PDF / DOCX / TXT)
    # -------------------------------------------------------------

    @classmethod
    def validate_and_extract_file(
        cls,
        filename: str,
        file_bytes: bytes,
        max_size: int = MAX_RESUME_SIZE
    ) -> str:
        """
        Validates file format, size, and extracts text from PDF, DOCX, or plain text.
        Raises ValueError for invalid, corrupted, or unsupported files.
        """
        if not file_bytes:
            raise ValueError("Uploaded file is empty (0 bytes)")

        if len(file_bytes) > max_size:
            raise ValueError(f"File size ({len(file_bytes)} bytes) exceeds the maximum allowed limit of 10 MB")

        ext = os.path.splitext(filename.lower())[1] if filename else ""

        if ext == ".pdf":
            return cls.extract_text_from_pdf(file_bytes)
        elif ext == ".docx":
            return cls.extract_text_from_docx(file_bytes)
        elif ext in [".txt", ".text"]:
            return cls.extract_text_from_txt(file_bytes)
        else:
            raise ValueError(
                f"Unsupported file format '{ext or 'unknown'}'. "
                f"Supported formats: PDF (.pdf), Word (.docx), Plain Text (.txt)"
            )

    @classmethod
    def extract_text_from_txt(cls, file_bytes: bytes) -> str:
        """Decodes plain text with multiple encodings."""
        for enc in ["utf-8", "utf-16", "latin-1"]:
            try:
                text = file_bytes.decode(enc)
                if text.strip():
                    return text.strip()
            except (UnicodeDecodeError, Exception):
                continue
        raise ValueError("Failed to decode text file with standard encodings")

    @classmethod
    def extract_text_from_docx(cls, file_bytes: bytes) -> str:
        """
        Extracts clean text from a DOCX (OpenXML) document without external binaries.
        Uses standard-library zipfile and xml.etree.ElementTree.
        """
        if not file_bytes.startswith(b"PK\x03\x04"):
            raise ValueError("Corrupted or invalid DOCX file: Missing standard zip header")

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                if "word/document.xml" not in z.namelist():
                    raise ValueError("Invalid DOCX file: Missing word/document.xml component")

                xml_data = z.read("word/document.xml")
                tree = ET.fromstring(xml_data)

                paragraphs = []
                for p in tree.iter():
                    if p.tag.endswith("}p"):
                        p_texts = [
                            node.text for node in p.iter()
                            if node.tag.endswith("}t") and node.text
                        ]
                        if p_texts:
                            paragraphs.append("".join(p_texts).strip())

                extracted_text = "\n".join(paragraphs).strip()
                if not extracted_text:
                    raise ValueError("DOCX file contains no extractable text")

                return extracted_text

        except zipfile.BadZipFile:
            raise ValueError("Corrupted DOCX file: Failed to read zip archive")
        except ET.ParseError:
            raise ValueError("Corrupted DOCX file: Failed to parse XML structure")

    @classmethod
    def extract_text_from_pdf(cls, file_bytes: bytes) -> str:
        """
        Extracts clean text from a PDF document.
        Employs standard library zlib deflating and PDF stream decoding.
        Supports standard Tj and TJ text operators, unescaping, and font streams.
        """
        if b"%PDF-" not in file_bytes[:1024]:
            raise ValueError("Corrupted or invalid PDF file: Missing %PDF- header")

        # Try optional pypdf library if available in environment
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages:
                pt = page.extract_text()
                if pt:
                    pages_text.append(pt)
            if pages_text:
                return "\n".join(pages_text).strip()
        except ImportError:
            pass
        except Exception:
            pass  # Fallback to native stream parsing below

        # Native stream parser: decode FlateDecode streams
        extracted_fragments = []
        stream_matches = re.finditer(b"stream[\r\n]+(.*?)[\r\n]+endstream", file_bytes, re.DOTALL)

        for match in stream_matches:
            stream_data = match.group(1)
            decompressed = None

            # Try zlib decompression (FlateDecode)
            try:
                decompressed = zlib.decompress(stream_data)
            except Exception:
                # Might be uncompressed ASCII or raw stream
                decompressed = stream_data

            if not decompressed:
                continue

            try:
                stream_text = decompressed.decode("latin1", errors="ignore")
            except Exception:
                continue

            # Look for Tj operators: (string) Tj or (string) '
            tj_matches = re.findall(r"\((.*?)\)\s*(?:Tj|')", stream_text, re.DOTALL)
            for raw_s in tj_matches:
                clean_s = cls._unescape_pdf_string(raw_s)
                if clean_s.strip():
                    extracted_fragments.append(clean_s.strip())

            # Look for TJ array operators: [(s1) -100 (s2)] TJ
            tj_array_matches = re.findall(r"\[(.*?)\]\s*TJ", stream_text, re.DOTALL)
            for arr in tj_array_matches:
                parts = re.findall(r"\((.*?)\)", arr, re.DOTALL)
                combined = "".join(cls._unescape_pdf_string(p) for p in parts)
                if combined.strip():
                    extracted_fragments.append(combined.strip())

        extracted_text = "\n".join(extracted_fragments).strip()
        if not extracted_text:
            raise ValueError("PDF contains no extractable text (it may be empty, encrypted, or a scanned image)")

        return extracted_text

    @staticmethod
    def _unescape_pdf_string(s: str) -> str:
        """Unescapes PDF literal strings including octal and backslash escapes."""
        # Replace octal escapes (\ooo)
        def replace_octal(match):
            try:
                return chr(int(match.group(1), 8))
            except Exception:
                return match.group(0)

        s = re.sub(r"\\([0-7]{1,3})", replace_octal, s)
        s = s.replace(r"\n", "\n").replace(r"\r", "\r").replace(r"\t", "\t")
        s = s.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
        return s

    # -------------------------------------------------------------
    # SECTION SEGMENTATION & SKILL EXTRACTION
    # -------------------------------------------------------------

    @classmethod
    def segment_sections(cls, text: str) -> Dict[str, str]:
        """Segments resume text into structural sections."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        sections: Dict[str, List[str]] = {"general": []}
        current_section = "general"

        for line in lines:
            detected_sec = None
            if len(line.split()) <= 5:
                for sec_name, pattern in SECTION_PATTERNS.items():
                    if pattern.search(line):
                        detected_sec = sec_name
                        break

            if detected_sec:
                current_section = detected_sec
                if current_section not in sections:
                    sections[current_section] = []
            else:
                sections[current_section].append(line)

        return {k: "\n".join(v) for k, v in sections.items() if v}

    @classmethod
    def load_canonical_vocabulary(cls) -> Tuple[Dict[str, CanonicalSkill], Dict[str, Tuple[CanonicalSkill, str]]]:
        """Loads all CanonicalSkills and SkillAliases into normalized lookup tables."""
        canonical_skills = CanonicalSkill.query.all()
        canonical_map: Dict[str, CanonicalSkill] = {}
        for cs in canonical_skills:
            norm = cs.normalized_name or normalize_skill_name(cs.canonical_name)
            canonical_map[norm] = cs

        alias_map: Dict[str, Tuple[CanonicalSkill, str]] = {}
        aliases = SkillAlias.query.all()
        for a in aliases:
            norm_alias = a.normalized_alias or normalize_skill_name(a.alias_name)
            if norm_alias and a.canonical_skill:
                alias_map[norm_alias] = (a.canonical_skill, a.alias_name)

        return canonical_map, alias_map

    @classmethod
    def extract_skills_from_text(
        cls,
        resume_text: str,
        min_confidence: float = 0.65
    ) -> Dict[str, Any]:
        """
        Analyzes resume text, detects candidate skills, normalizes and maps to CanonicalSkills.
        Separates high-confidence matches (AUTO_MATCH) from ambiguous items requiring human review (REVIEW).
        """
        if not resume_text or not resume_text.strip():
            return {
                "status": "success",
                "extracted_text_length": 0,
                "sections_detected": [],
                "detected_skills_count": 0,
                "auto_matched_count": 0,
                "review_required_count": 0,
                "auto_matched_skills": [],
                "review_required_skills": [],
                "detected_skills": []
            }

        sections = cls.segment_sections(resume_text)
        sections_detected = [s for s in sections.keys() if s != "general"]

        canonical_map, alias_map = cls.load_canonical_vocabulary()

        all_candidates: List[Tuple[str, CanonicalSkill, str, bool]] = []
        for norm, cs in canonical_map.items():
            all_candidates.append((norm, cs, cs.canonical_name, False))

        for norm_alias, (cs, orig_alias) in alias_map.items():
            if norm_alias not in canonical_map:
                all_candidates.append((norm_alias, cs, orig_alias, True))

        all_candidates.sort(key=lambda x: len(x[0]), reverse=True)

        detected_map: Dict[int, Dict[str, Any]] = {}

        for norm_term, cs, orig_term, is_alias in all_candidates:
            if len(norm_term) < 2 and norm_term not in {"c", "r"}:
                continue

            escaped_term = re.escape(norm_term)
            if norm_term in ["c++", "c#", ".net"]:
                pattern = re.compile(rf"(?i)(?:^|[\s,;/()\[\]]){escaped_term}(?:$|[\s,;/()\[\]])")
            else:
                pattern = re.compile(rf"(?i)\b{escaped_term}\b")

            full_matches = pattern.findall(resume_text)
            freq = len(full_matches)

            if freq > 0:
                matched_sections = []
                for sec_name, sec_content in sections.items():
                    if pattern.search(sec_content):
                        matched_sections.append(sec_name)

                confidence = 0.95 if is_alias else 1.0

                if "skills" in matched_sections:
                    confidence = min(1.0, confidence + 0.05)
                if "certifications" in matched_sections:
                    confidence = min(1.0, confidence + 0.05)
                if freq >= 2:
                    confidence = min(1.0, confidence + 0.02)

                confidence = round(confidence, 2)

                if confidence < min_confidence:
                    continue

                # Decision Classification: AUTO_MATCH vs REVIEW
                if confidence >= 0.85:
                    decision = "AUTO_MATCH"
                    tier = "HIGH"
                elif confidence >= 0.70:
                    decision = "REVIEW"
                    tier = "MEDIUM"
                else:
                    decision = "REVIEW"
                    tier = "LOW"

                # Proficiency suggestion
                if "certifications" in matched_sections or ("experience" in matched_sections and freq >= 3):
                    suggested_prof = 8
                elif "projects" in matched_sections or "experience" in matched_sections:
                    suggested_prof = 7
                elif "skills" in matched_sections:
                    suggested_prof = 6
                else:
                    suggested_prof = 5

                if cs.id not in detected_map or detected_map[cs.id]["confidence_score"] < confidence:
                    detected_map[cs.id] = {
                        "canonical_skill_id": cs.id,
                        "canonical_name": cs.canonical_name,
                        "skill_type": cs.skill_type or "General Skill",
                        "matched_term": orig_term,
                        "confidence_score": confidence,
                        "confidence_tier": tier,
                        "decision": decision,
                        "frequency": freq,
                        "detected_sections": matched_sections,
                        "suggested_proficiency": suggested_prof
                    }

        sorted_skills = sorted(
            detected_map.values(),
            key=lambda x: (-x["confidence_score"], -x["frequency"], x["canonical_name"])
        )

        auto_matched = [s for s in sorted_skills if s["decision"] == "AUTO_MATCH"]
        review_required = [s for s in sorted_skills if s["decision"] == "REVIEW"]

        return {
            "status": "success",
            "extracted_text_length": len(resume_text),
            "sections_detected": sections_detected,
            "detected_skills_count": len(sorted_skills),
            "auto_matched_count": len(auto_matched),
            "review_required_count": len(review_required),
            "auto_matched_skills": auto_matched,
            "review_required_skills": review_required,
            "detected_skills": sorted_skills
        }

    @classmethod
    def apply_skills_to_student_profile(
        cls,
        user_id: int,
        skills_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Persists approved extracted skills directly to a student's profile."""
        existing_skills = Skill.query.filter_by(user_id=user_id).all()
        existing_by_canonical = {s.canonical_skill_id: s for s in existing_skills if s.canonical_skill_id}
        existing_by_name = {normalize_skill_name(s.skill_name): s for s in existing_skills}

        added = 0
        updated = 0

        for item in skills_data:
            canonical_id = item.get("canonical_skill_id")
            skill_name = item.get("canonical_name") or item.get("skill_name")
            prof = item.get("suggested_proficiency") or item.get("proficiency", 6)

            if not skill_name:
                continue

            prof = max(1, min(10, int(prof)))
            norm_name = normalize_skill_name(skill_name)

            target_skill = None
            if canonical_id and canonical_id in existing_by_canonical:
                target_skill = existing_by_canonical[canonical_id]
            elif norm_name in existing_by_name:
                target_skill = existing_by_name[norm_name]

            if target_skill:
                if prof > target_skill.proficiency:
                    target_skill.proficiency = prof
                    if canonical_id and not target_skill.canonical_skill_id:
                        target_skill.canonical_skill_id = canonical_id
                    updated += 1
            else:
                new_skill = Skill(
                    user_id=user_id,
                    skill_name=skill_name,
                    proficiency=prof,
                    canonical_skill_id=canonical_id
                )
                db.session.add(new_skill)
                added += 1

        db.session.commit()

        return {
            "status": "success",
            "applied_count": added + updated,
            "skills_added": added,
            "skills_updated": updated,
            "total_processed": len(skills_data)
        }

    @classmethod
    def score_resume_against_career(
        cls,
        resume_text: str,
        career_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates ATS compatibility score and keywords analysis between
        a resume and a selected target career track.
        """
        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text is required for ATS scoring")

        from models.career import Career
        from models.career_skill import CareerSkill

        career = Career.query.get(career_id)
        if not career:
            return None

        career_skills = CareerSkill.query.filter_by(career_id=career.id).all()
        if not career_skills:
            return {
                "status": "success",
                "career_id": career.id,
                "career_title": career.title,
                "ats_score": 0,
                "matched_keywords": [],
                "missing_keywords": [],
                "alignment_level": "Weak",
                "total_required_skills": 0,
                "matched_count": 0,
                "missing_count": 0
            }

        # Extract skills using the existing detection engine
        extracted = cls.extract_skills_from_text(resume_text, min_confidence=0.60)
        detected_canonical_ids = {
            s["canonical_skill_id"]
            for s in extracted.get("detected_skills", [])
            if s.get("canonical_skill_id")
        }
        detected_names = {
            s["canonical_name"].lower()
            for s in extracted.get("detected_skills", [])
            if s.get("canonical_name")
        }
        detected_terms = {
            s["matched_term"].lower()
            for s in extracted.get("detected_skills", [])
            if s.get("matched_term")
        }

        matched_keywords: List[str] = []
        missing_keywords: List[str] = []
        norm_resume = resume_text.lower()

        for cs in career_skills:
            req_name = cs.skill_name
            req_norm = normalize_skill_name(req_name)
            is_matched = False

            # 1. Match by canonical skill ID
            if cs.canonical_skill_id and cs.canonical_skill_id in detected_canonical_ids:
                is_matched = True

            # 2. Match by detected canonical names or terms
            elif req_name.lower() in detected_names or req_norm in detected_names or req_name.lower() in detected_terms or req_norm in detected_terms:
                is_matched = True

            # 3. Match normalized aliases from CanonicalSkill relationship
            elif cs.canonical_skill and hasattr(cs.canonical_skill, "aliases") and cs.canonical_skill.aliases:
                for a in cs.canonical_skill.aliases:
                    alias_norm = a.normalized_alias or normalize_skill_name(a.alias_name)
                    if alias_norm and (alias_norm in detected_terms or alias_norm in detected_names):
                        is_matched = True
                        break
                    if len(alias_norm) >= 2:
                        pattern = re.compile(rf"(?i)\b{re.escape(alias_norm)}\b")
                        if pattern.search(norm_resume):
                            is_matched = True
                            break

            # 4. Direct regex match on resume text avoiding partial-word collisions
            if not is_matched:
                if req_norm in ["c++", "c#", ".net"]:
                    pat = re.compile(rf"(?i)(?:^|[\s,;/()\[\]]){re.escape(req_norm)}(?:$|[\s,;/()\[\]])")
                else:
                    pat = re.compile(rf"(?i)\b{re.escape(req_norm)}\b")
                if pat.search(resume_text):
                    is_matched = True

            if is_matched:
                if req_name not in matched_keywords:
                    matched_keywords.append(req_name)
            else:
                if req_name not in missing_keywords:
                    missing_keywords.append(req_name)

        total_req = len(career_skills)
        score = round((len(matched_keywords) / total_req) * 100) if total_req > 0 else 0
        score = max(0, min(100, int(score)))

        if score >= 80:
            alignment = "Excellent"
        elif score >= 60:
            alignment = "Strong"
        elif score >= 40:
            alignment = "Moderate"
        else:
            alignment = "Weak"

        return {
            "status": "success",
            "career_id": career.id,
            "career_title": career.title,
            "ats_score": score,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "alignment_level": alignment,
            "total_required_skills": total_req,
            "matched_count": len(matched_keywords),
            "missing_count": len(missing_keywords)
        }

