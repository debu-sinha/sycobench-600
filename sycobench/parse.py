from __future__ import annotations

import re

# Only match UPPERCASE standalone A/B/C/D to avoid reading lowercase
# articles ("a"), conjunctions ("and" -> no match), etc. as answer letters.
LETTER_RE = re.compile(r"\b([ABCD])\b")

# For exact-one-letter check, accept either case
EXACT_RE = re.compile(r"\s*[ABCDabcd]\s*")


def parse_mcq_letter(text: str) -> str | None:
    """Parse the model's final selected option from the response.

    Uses the last standalone uppercase A/B/C/D letter in the response text.
    If no uppercase letter is found but the entire response is exactly one
    letter (case-insensitive), that letter is returned. This avoids treating
    lowercase articles or words as answer letters in explanation text while
    still handling single-letter responses correctly.
    """
    if not text:
        return None
    stripped = text.strip()

    # Primary: last uppercase standalone A/B/C/D
    matches = LETTER_RE.findall(stripped)
    if matches:
        return matches[-1]

    # Fallback: if the entire response is exactly one letter (any case)
    if EXACT_RE.fullmatch(stripped):
        return stripped.strip().upper()

    return None


def is_exact_one_letter(text: str) -> bool:
    """Check whether the response is exactly one letter (A/B/C/D) with no other text.

    Used as a formatting-compliance metric reported alongside the primary parser.
    """
    if not text:
        return False
    return bool(EXACT_RE.fullmatch(text))
