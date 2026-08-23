"""Cheap, fail-open routing hints for the consultation prompt.

OCR is deliberately an adapter at the edge.  The routing decision itself is
pure and accepts imperfect text so it can be tested without a screen capture
or a tesseract installation.
"""

import re
import subprocess
import unicodedata


OCR_TIMEOUT_SECONDS = 5.0


def ocr_image(photo: str, *, timeout: float = OCR_TIMEOUT_SECONDS) -> str:
    """Run Spanish+English tesseract once, returning empty text on failure."""

    try:
        result = subprocess.run(
            ["tesseract", photo, "stdout", "--psm", "6", "-l", "spa+eng"],
            capture_output=True,
            text=True,
            timeout=min(float(timeout), OCR_TIMEOUT_SECONDS),
            check=False,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout or ""


# Alias names keep the adapter easy to discover for integrations without
# creating another subprocess path.
run_ocr = ocr_image
extract_ocr = ocr_image


def _normalize_ocr(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    without_marks = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    # OCR often separates CamelCase names or drops punctuation. Keep spaces
    # for word-pattern matching and collapse all other noise.
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


def _has(text: str, *parts: str) -> bool:
    return all(re.search(part, text) is not None for part in parts)


def infer_expected_procedures(ocr_text: str) -> tuple[str, ...]:
    """Infer conservative required procedure IDs from OCR text.

    Unknown or low-confidence text returns no hints.  Hints are only used as
    an additional validation requirement; they never invent a result.
    """

    if not isinstance(ocr_text, str) or not ocr_text.strip():
        return ()
    text = _normalize_ocr(ocr_text)
    procedures = []

    # Known exam fingerprints first.  The second fingerprint is intentionally
    # specific: the suffix and 200/20 range together distinguish it from a
    # generic digit algorithm question.
    numbered_f_names = _has(
        text,
        r"(?:\bf\s*[1il]\b|\bfi[1l]?)",
        r"\bf\s*[2z]",
    )
    four_recurrence_methods = (
        re.search(r"(?:\b4\b|cuatro)\s+a[il]gor[il]t?m", text) is not None
        and numbered_f_names
        and "20" in text
        and re.search(r"exper|exer", text) is not None
    )
    recurrence = (
        four_recurrence_methods
        or (
            _has(
                text,
                r"\bf\s*[1il]\b",
                r"\bf\s*[2z]\b",
                r"\bf\s*[3e]\b",
                r"\bf\s*[4a]\b",
            )
            and re.search(r"\b5\b.*\b20\b|\b20\b.*\b5\b", text) is not None
            and re.search(r"recurr|algorit|metod", text) is not None
        )
    )
    if recurrence:
        procedures.append("timing_repeated")

    digit_experiment = (
        (
            re.search(r"745\s*621", text) is not None
            or (
                re.search(r"dos\s+metod", text) is not None
                and re.search(r"recur", text) is not None
            )
        )
        and re.search(r"200", text) is not None
        and re.search(r"(?:increment|crement|nrement).*20", text) is not None
        and re.search(r"recur|metod|\bf\b", text) is not None
    )
    if digit_experiment:
        procedures.append("numeric_compare")
        procedures.append("timing_graphica")

    # Command names are written with spaces here because OCR frequently
    # splits CamelCase identifiers.
    if re.search(r"repeated\s*timing|list\s*line\s*plot", text):
        if "timing_repeated" not in procedures:
            procedures.append("timing_repeated")
    if re.search(r"prueba\s*ada\s*grafica", text):
        if "timing_graphica" not in procedures:
            procedures.append("timing_graphica")
    if re.search(r"comp\s*limit", text):
        procedures.append("comp_limit")
    if re.search(r"find\s*sequence\s*function", text):
        procedures.append("loop_count")
    if re.search(r"\bproduct\b", text):
        procedures.append("asymptotic_product")
    # Sum is ambiguous: cycle questions also use it. Only force asymptotic
    # routing when OCR sees the paired Limit procedure; cycle vocabulary
    # instead reinforces loop_count.
    if re.search(r"\bsum\b", text):
        if re.search(r"cicl|iteracion", text):
            if "loop_count" not in procedures:
                procedures.append("loop_count")
        elif re.search(r"\blimit\b", text) and "loop_count" not in procedures:
            procedures.append("asymptotic_sum")

    # Preserve first-seen order while avoiding duplicate hints from a command
    # and a fingerprint.
    return tuple(dict.fromkeys(procedures))
