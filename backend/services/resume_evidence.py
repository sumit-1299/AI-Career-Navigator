"""Resume mentions remain document claims, never verified proficiency."""
import re
from services.skill_catalog import SKILLS, keyword_keys

POLICY_VERSION = "resume-mentions-v1"
# Deliberately conservative. Keep excluded passages available for the user to review.
UNCERTAIN = re.compile(r"\b(?:no|not|without|never|learning|learn|interested|interest|aspiring|seeking|beginner|exposure)\b", re.I)


def analyze_resume(text):
    mentions = {item["key"]: [] for item in SKILLS}
    review = []
    for raw in re.split(r"[\r\n]+|(?<=[.!?;])\s+", text):
        line = raw.strip()
        if not line:
            continue
        # Keep bounded complete excerpts, including skill matches late in a long line.
        words = line.split()
        for start in range(0, len(words), 50):
            passage = " ".join(words[start:start + 50])
            keys = keyword_keys(passage)
            if not keys:
                continue
            if UNCERTAIN.search(line):
                review.append({"text": passage, "reason": "Learning, interest or negative wording; review before treating it as experience."})
                continue
            for key in keys:
                if passage not in mentions[key]:
                    mentions[key].append(passage)
    return {"policy_version": POLICY_VERSION,
            "skills": [{"skill_key": s["key"], "label": s["label"], "passages": mentions[s["key"]]}
                       for s in SKILLS if mentions[s["key"]]],
            "manual_review": review,
            "interpretation": "Literal mentions in ten supported skill concepts. Review extracted text. Mentions are unverified claims, not proof of proficiency."}


def alignment_summary(rows, has_resume):
    explicit = [row for row in rows if row["mapping"] == "keyword"]
    def has_evidence(row):
        return any(c["kind"] in {"project", "certification"} for c in row["candidate_claims"])
    def answered(row):
        return bool(row["assessment"] and row["assessment"]["result"]["answered_count"])
    return {"version": "source-coverage-v1", "resume_included": has_resume,
            "named_skills": len(explicit),
            "with_resume_mentions": sum(bool(r["resume_mentions"]) for r in explicit),
            "with_self_ratings": sum(any(c["kind"] == "self_report" for c in r["candidate_claims"]) for r in explicit),
            "with_project_or_certificate": sum(has_evidence(r) for r in explicit),
            "with_answered_diagnostic": sum(answered(r) for r in explicit),
            "without_recorded_support": [r["label"] for r in explicit if not (r["resume_mentions"] or r["candidate_claims"] or answered(r))],
            "interpretation": "Counts use only named job skills in the supported catalogue, including preferred mentions. Sources can overlap. Semantic suggestions are excluded; these are coverage counts, not a job-fit score."}
