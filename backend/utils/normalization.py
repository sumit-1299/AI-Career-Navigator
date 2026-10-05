"""
Unified Normalization Utility for AI Career Navigator.

Provides centralized, deterministic string normalization and cleaning
for skills, competencies, knowledge areas, tools, and aliases across
all data sources (O*NET 31.0, ESCO 1.2.1, NSDC, and student inputs).
"""

import re
import unicodedata
from typing import Optional


def normalize_skill_name(value: Optional[str]) -> str:
    """
    Deterministically normalize a skill name for indexing and comparison.

    Performs:
    1. Type safety check (returns empty string if None or non-string).
    2. Unicode normalization via NFKC.
    3. Safe trimming of leading and trailing whitespace.
    4. Lowercase conversion.
    5. Collapsing consecutive whitespace characters to a single space.

    Preserves:
    - Meaningful programming symbols:
      '+' (e.g., 'C++', 'C++17')
      '#' (e.g., 'C#', 'F#')
      '.' (e.g., '.NET', 'Node.js', 'Vue.js')
      '/' (e.g., 'CI/CD', 'TCP/IP', 'PL/SQL')
      '-' (e.g., 'Front-End', 'Back-End', 'Scikit-Learn')
    """
    if value is None:
        return ""

    if not isinstance(value, str):
        value = str(value)

    # Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", value)

    # Safe trim and lowercase
    normalized = normalized.strip().lower()

    # Collapse all whitespace sequences
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def strip_parenthetical_qualifiers(value: Optional[str]) -> str:
    """
    Strips trailing taxonomic parenthetical qualifiers while preserving core terminology.

    Example:
        'Python (computer programming)' -> 'Python'
        'Java (software platform)' -> 'Java'
    """
    if not value or not isinstance(value, str):
        return ""

    stripped = value.strip()
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", stripped).strip()
    return cleaned if cleaned else stripped


def is_exact_match(value1: Optional[str], value2: Optional[str]) -> bool:
    """
    Check if two skill strings are identical after unified normalization.
    """
    norm1 = normalize_skill_name(value1)
    norm2 = normalize_skill_name(value2)

    if not norm1 or not norm2:
        return False

    return norm1 == norm2


def is_ambiguous_match(name1: Optional[str], name2: Optional[str]) -> bool:
    """
    Identify potential semantic conflicts or partial overlap that should
    NOT be automatically merged without human review.

    Example:
        'Cloud Management' vs 'Cloud Computing' -> True (Ambiguous overlap)
        'Machine Learning' vs 'Machine Learning Engineering' -> True
    """
    norm1 = normalize_skill_name(name1)
    norm2 = normalize_skill_name(name2)

    if not norm1 or not norm2 or norm1 == norm2:
        return False

    # Check for substring containment
    if norm1 in norm2 or norm2 in norm1:
        return True

    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())

    if not tokens1 or not tokens2:
        return False

    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)

    # Any shared meaningful word between multi-word skill phrases indicates ambiguity
    if intersection and (len(tokens1) > 1 or len(tokens2) > 1):
        return True

    similarity = len(intersection) / len(union)
    return similarity >= 0.3
