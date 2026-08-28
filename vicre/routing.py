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


# Keyword families per cuadernillo chapter, matched against normalized text
# (lowercase, accents stripped, punctuation collapsed to spaces).  Families
# are intentionally chapter-granular: a coarse but precise hint is more
# useful to the model than a fragile one.
_CHAPTER_KEYWORDS = (
    ("cap1", (r"recursiv", r"de pila", r"de cola", r"fibonacci", r"factorial", r"casos ?raiz")),
    ("cap2", (r"recurrencia", r"homogenea", r"ecuacion ?caracteristica", r"metodo ?rrhl", r"findrrhl", r"raices ?distintas")),
    ("cap3", (r"algoritmo", r"o grande", r"asintot", r"eficiencia", r"repeated ?timing", r"list ?line ?plot", r"pruebaada", r"experimento")),
    ("cap4", (r"relacion ?binaria", r"matriz ?de ?la ?relacion", r"equivalencia", r"producto ?cartesiano", r"clasificar ?relacion")),
    ("cap5", (r"grafo", r"trayectoria", r"circuito", r"euler", r"hamilton", r"camino ?mas ?corto", r"ruta")),
    ("cap6", (r"arbol", r"huffman", r"polaca", r"arbol ?generador", r"expansion ?minima")),
    ("cap7", (r"automata", r"maquina ?de ?estados", r"hilera", r"afd", r"aef")),
    ("cap8", (r"gramatica", r"lenguaje", r"bnf", r"derivacion", r"libre ?de ?contexto")),
)


def infer_expected_procedures(ocr_text: str) -> tuple[str, ...]:
    """Infer conservative cuadernillo chapter IDs from OCR text.

    Unknown or low-confidence text returns no hints.  Hints are only used as
    an additional validation requirement; they never invent a result.
    """

    if not isinstance(ocr_text, str) or not ocr_text.strip():
        return ()
    text = _normalize_ocr(ocr_text)
    procedures = []
    for chapter_id, keywords in _CHAPTER_KEYWORDS:
        if any(re.search(keyword, text) is not None for keyword in keywords):
            procedures.append(chapter_id)
    return tuple(procedures)
