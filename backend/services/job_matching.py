"""Explainable keyword baseline and conservative semantic skill suggestions."""

import re

from services.semantic_encoder import MODEL_ID, MODEL_REVISION, get_encoder
from services.skill_catalog import BY_KEY, CATALOG_VERSION, RELATIONS, SKILLS, canonical_key, keyword_keys
from services.resume_evidence import analyze_resume, alignment_summary

POLICY_VERSION = "pasted-job-comparison-v2"
EXTRACTION_VERSION = "skill-extraction-context-v2"
SIMILARITY_THRESHOLD = 0.58
MARGIN_THRESHOLD = 0.08
NEGATION = re.compile(r"\b(no|not|without|never|neither|nor|cannot)\b|\b(?:isn|aren|wasn|weren|don|doesn|didn|needn|mustn|shouldn|can|couldn|wouldn|won)['’]t\b", re.I)
OPTIONAL = re.compile(r"\b(preferred|optional|bonus|desirable)\b|nice[ -]to[ -]have", re.I)
REQUIRED = re.compile(r"\b(required|requirements|essential|must)\b|minimum qualifications", re.I)

REQUIRED_HEADINGS = {"requirements", "required skills", "minimum qualifications", "must have",
    "qualifications", "what we are looking for", "what we are looking for in you",
    "who you are", "what you bring", "your skills", "skills and experience"}
OPTIONAL_HEADINGS = {"preferred", "preferred skills", "nice to have", "nice-to-have", "optional",
    "nice-to-have skills", "nice-to-have skills we would value", "additional skills",
    "additional skills that you might also bring"}
ROLE_HEADINGS = {"responsibilities", "about the role", "the role entails", "what you will do",
    "what you'll do", "what you’ll do", "what your day will look like", "what you will focus on",
    "your role", "duties"}
BACKGROUND_HEADINGS = {"about us", "about the company", "company overview", "company background",
    "our company", "benefits", "what we offer", "what we offer you", "what we offer colleagues",
    "about our company", "who we are"}
# This is a narrow wording rule, not named-entity recognition. It does not contain
# employer names or case IDs from the development packet.
PORTFOLIO_STATEMENT = re.compile(
    r"^.{1,80}?\b(?:has|have)\s+(?:(?:substantial|many|several|numerous|existing|various|multiple)\s+)?"
    r"(?:projects|products)\s+(?:in|using|built with)\b", re.I)
COMPANY_STATEMENT = re.compile(
    r"^(?:(?:our|the)\s+(?:company|business|organisation|organization))\s+"
    r"(?:uses?|offers?|provides?|develops?|builds?|maintains?)\b", re.I)
ROLE_REFERENCE = re.compile(
    r"\b(?:you|your|candidates?|applicants?|this role|the role|this position|the position|"
    r"this job|the team|our team)\b", re.I)
ROLE_ACTION = re.compile(
    r"^(?:design|build|write|develop|maintain|implement|use|work|operate|deploy|manage|lead|"
    r"create|test|debug|support|contribute|architect|improve)\b", re.I)
ROLE_QUALIFICATION = re.compile(r"^(?:experience|knowledge|proficiency|familiarity|skills?)\s+(?:with|in|of)\b", re.I)
# Split a mixed company/candidate sentence only at an explicit candidate clause.
# General mixed negation remains subject to the existing manual-review policy.
PASSAGE_BOUNDARY = re.compile(
    r"[\r\n;]+|(?<=[.!?])\s+|,?\s+\b(?:and|but|while|whereas)\s+"
    r"(?=(?:you\b|your\b|this role\b|the role\b|this position\b|the position\b))", re.I)


def review_context(text, background):
    if NEGATION.search(text):
        return "negation", "Negation detected; read this passage before treating it as a requirement."
    role_link = ROLE_REFERENCE.search(text) or ROLE_ACTION.search(text) or ROLE_QUALIFICATION.search(text)
    if not role_link and (PORTFOLIO_STATEMENT.search(text) or COMPANY_STATEMENT.search(text)):
        return "company_context", "Company or product-portfolio wording. Confirm that this skill applies to the candidate's work."
    if background and not (role_link or REQUIRED.search(text) or OPTIONAL.search(text)):
        return "background_section", "Company-background or benefits section. Confirm a role-specific requirement before using this passage."
    return None, None


def fragments(description, max_fragments=60):
    parts = []
    priority = "mentioned"
    background = False
    for raw in PASSAGE_BOUNDARY.split(description):
        text = raw.strip(" \t•*-–—")
        if not text:
            continue
        heading = text.rstrip(":").casefold()
        if heading in REQUIRED_HEADINGS:
            priority = "required"
            background = False
            continue
        if heading in OPTIONAL_HEADINGS:
            priority = "optional"
            background = False
            continue
        if heading in ROLE_HEADINGS:
            priority = "mentioned"
            background = False
            continue
        if heading in BACKGROUND_HEADINGS:
            priority = "mentioned"
            background = True
            continue
        importance = "optional" if OPTIONAL.search(text) else "required" if REQUIRED.search(text) else priority
        review_code, review_reason = review_context(text, background)
        # Bound each input while retaining every fragment. The encoder also rejects token overflow.
        words = text.split()
        for start in range(0, len(words), 45):
            snippet = " ".join(words[start:start + 45])
            parts.append({"text": snippet, "importance": importance,
                          "review_needed": review_reason is not None,
                          "review_code": review_code, "review_reason": review_reason})
    if len(parts) > max_fragments:
        raise ValueError(f"This description exceeds the {max_fragments}-fragment comparison limit. Use a shorter excerpt in Compare a job; the full posting has not been compared.")
    return parts


def profile_support(snapshot):
    support = {key: [] for key in BY_KEY}
    unmapped = []
    for claim in snapshot["skills"]:
        key = canonical_key(claim["skill_name"])
        if key:
            support[key].append({"kind": "self_report", "record_id": claim["id"],
                                 "label": claim["skill_name"], "rating": claim["proficiency"]})
        else:
            unmapped.append(claim["skill_name"])
    for item in snapshot["evidence"]:
        for tag in item["skills"]:
            key = canonical_key(tag)
            if key:
                support[key].append({"kind": item["kind"], "record_id": item["id"], "version": item["version"],
                                     "label": item["title"], "tag": tag, "verification_status": "unverified"})
            else:
                unmapped.append(tag)
    return support, sorted(set(unmapped), key=str.casefold)


def build_comparison(description, snapshot, mode, encoder=None, max_fragments=60):
    parts = fragments(description, max_fragments)
    if not parts:
        raise ValueError("Enter a job description containing words.")
    suggestions = {}
    if mode == "semantic":
        encoder = encoder or get_encoder()
        safe = [(i, part) for i, part in enumerate(parts) if not part["review_needed"]]
        vectors = encoder.encode([skill["anchor"] for skill in SKILLS] + [part["text"] for _, part in safe])
        anchors = vectors[:len(SKILLS)]
        for (index, _), vector in zip(safe, vectors[len(SKILLS):]):
            ranked = sorted([(sum(a * b for a, b in zip(vector, anchor)), skill["key"])
                             for skill, anchor in zip(SKILLS, anchors)], reverse=True)
            score, key = ranked[0]
            margin = score - ranked[1][0]
            if score >= SIMILARITY_THRESHOLD and margin >= MARGIN_THRESHOLD:
                suggestions[index] = {"skill_key": key, "similarity": round(score, 4), "margin": round(margin, 4)}
    rows = {}
    unassigned = []
    manual_review = []
    for index, part in enumerate(parts):
        if part["review_needed"]:
            manual_review.append({"text": part["text"], "reason": part["review_reason"],
                                  "reason_code": part["review_code"]})
            continue
        direct = keyword_keys(part["text"])
        found = [(key, {"method": "keyword", "text": part["text"], "importance": part["importance"]}) for key in direct]
        inferred = suggestions.get(index)
        if inferred and inferred["skill_key"] not in direct:
            found.append((inferred["skill_key"], {"method": "semantic_suggestion", "text": part["text"],
                                                 "importance": part["importance"], "similarity": inferred["similarity"], "margin": inferred["margin"]}))
        if not found:
            unassigned.append(part["text"])
        for key, source in found:
            rows.setdefault(key, []).append(source)
    support, unmapped_claims = profile_support(snapshot)
    resume = snapshot.get("resume")
    resume_analysis = analyze_resume(resume["text"]) if resume else None
    resume_mentions = {row["skill_key"]: row["passages"] for row in resume_analysis["skills"]} if resume_analysis else {}
    result_rows = []
    for skill in SKILLS:
        key = skill["key"]
        if key not in rows:
            continue
        direct_sources = [source for source in rows[key] if source["method"] == "keyword"]
        related = []
        for relation in RELATIONS:
            if relation["target"] == key:
                related.extend({**claim, "skill_label": BY_KEY[relation["source"]]["label"], "relation": relation["relation"]}
                               for claim in support[relation["source"]])
        assessment = snapshot.get("assessments", {}).get(key)
        if assessment is None and key == "sql":
            assessment = snapshot.get("sql_assessment")
        if assessment and assessment["result"]["incorrect_count"]:
            guidance = f"Review the {skill['label']} topic results and practise the topics answered incorrectly. This small diagnostic does not establish overall proficiency."
        elif assessment and assessment["result"]["answered_count"] and assessment["result"]["unanswered_count"]:
            guidance = f"The answered {skill['label']} questions were correct, but some questions remain unassessed. Collect fresh evidence for those topics."
        elif assessment and assessment["result"]["answered_count"]:
            guidance = f"All questions in this {skill['label']} attempt were answered correctly. That describes this small diagnostic; use fresh practical tasks for broader evidence."
        elif assessment:
            guidance = f"The {skill['label']} attempt was entirely skipped. This skill remains unassessed; collect more evidence."
        elif support[key] or resume_mentions.get(key):
            guidance = "A candidate claim is recorded. Collect an independent assessment or review before treating proficiency as established."
        else:
            guidance = "No matching claim or assessment is recorded. Ask for evidence; absence of a record does not establish a skill deficit."
        result_rows.append({"skill_key": key, "label": skill["label"], "esco_uri": skill["esco_uri"],
                            "mapping": "keyword" if direct_sources else "semantic_suggestion",
                            "job_sources": rows[key], "candidate_claims": support[key], "related_claims": related,
                            "resume_mentions": resume_mentions.get(key, []),
                            "assessment": assessment, "guidance": guidance})
    direct_rows = [row for row in result_rows if row["mapping"] == "keyword"]
    return {"policy_version": POLICY_VERSION, "extraction_version": EXTRACTION_VERSION,
            "catalog_version": CATALOG_VERSION, "mode": mode,
            "candidate_evidence_version": "latest-per-skill-v2",
            "resume_analysis": resume_analysis,
            "alignment": alignment_summary(result_rows, bool(resume)),
            "model": {"id": MODEL_ID, "revision": MODEL_REVISION, "runtime": "onnx-cpu", "pooling": "attention-mask-mean-l2", "max_tokens": 256} if mode == "semantic" else None,
            "suggestion_policy": {"minimum_cosine": SIMILARITY_THRESHOLD, "minimum_margin": MARGIN_THRESHOLD,
                                  "validation_status": "heuristic_not_calibrated"} if mode == "semantic" else None,
            "summary": {"explicit_skill_mentions": len(direct_rows),
                        "explicit_mentions_with_claims": sum(bool(row["candidate_claims"]) for row in direct_rows),
                        "semantic_suggestions": sum(row["mapping"] == "semantic_suggestion" for row in result_rows),
                        "skills_with_assessment_records": sum(row["assessment"] is not None for row in result_rows)},
            "skills": result_rows, "unassigned_fragments": unassigned, "manual_review": manual_review,
            "unmapped_candidate_tags": unmapped_claims,
            "scope": "Ten backend-related skill concepts. Unmatched text may contain important requirements outside this catalogue.",
            "interpretation": "This is a saved comparison of text and candidate records, not a hiring probability or validated proficiency score. Semantic suggestions need review. Unverified evidence remains a claim."}
