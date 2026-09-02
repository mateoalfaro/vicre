"""Extract the master cuadernillo PDF into navigable Markdown chunks.

Build-time tool (Nix): the model never reads the 461-page PDF; it greps and
reads the deterministic text chunks produced here.  The core, ``split_pages``,
is pure and unit-tested; only ``main`` touches pypdf.

Usage: python tools/extract_fuentes.py <pdf> <outdir>
"""

import argparse
import os
import re
import sys


PART_TITLES = {
    "PRIMERA PARTE": ("ejercicios", "Los ejercicios"),
    "SEGUNDA PARTE": ("respuestas", "Las respuestas"),
    "TERCERA PARTE": ("complementarios", "Ejercicios complementarios, resueltos"),
    "CUARTA PARTE": ("tipo-examen", "Preguntas tipo examen"),
}

CHAPTER_NAMES = {
    "1": "Recursividad",
    "2": "Relaciones de recurrencia",
    "3": "Análisis de algoritmos",
    "4": "Relaciones binarias",
    "5": "Teoría de grafos",
    "6": "Teoría de árboles",
    "7": "Máquinas de estado finito y autómatas",
    "8": "Lenguajes y gramáticas",
}

APPENDIX_FILES = {
    "A": "apendice-a.md",
    "B": "apendice-b.md",
    "C": "apendice-c.md",
}

APPENDIX_TITLES = {
    "A": "Los recursos del curso",
    "B": "Índice de funciones de VilCretas",
    "C": "Mapa de estudio y simulacros",
}

_PART_RE = re.compile(r"^\s*(PRIMERA|SEGUNDA|TERCERA|CUARTA)\s+PARTE\s*$", re.MULTILINE)
_CHAPTER_RE = re.compile(
    r"^\s*Cap[íi]tulo\s+([1-8])(?=[\s.·•])", re.IGNORECASE | re.MULTILINE
)
_NAMES = "|".join(re.escape(name) for name in CHAPTER_NAMES.values())
_CHAPTER_HEADER_RE = re.compile(
    rf"^\s*({_NAMES})\s+Ejercicios y respuestas\s*$", re.MULTILINE
)
_NAME_TO_CHAPTER = {name: number for number, name in CHAPTER_NAMES.items()}
_APPENDIX_RE = re.compile(
    r"^\s*AP[ÉE]NDICE\s+([ABC])\s*$|^\s*Ap[ée]ndice\s+([ABC])\s*\.",
    re.IGNORECASE | re.MULTILINE,
)
_PAGE_NUM_RE = re.compile(r"^\s*(?:\d{1,3}|[ivxlc]+)\s*$", re.IGNORECASE)
_RUNNING_HEADER_RE = re.compile(r"^\s*.*Ejercicios y respuestas\s*$", re.MULTILINE)
_CATEGORY_RE = re.compile(r"Categor[íi]a del banco:\s*(.+)")
_FUNCTION_ROW_RE = re.compile(r"^([A-Z][A-Za-z0-9]+)\s+\d", re.MULTILINE)


def _clean_page(text):
    text = _RUNNING_HEADER_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    lines = [line for line in text.splitlines() if not _PAGE_NUM_RE.fullmatch(line)]
    return "\n".join(lines).strip("\n")


def _classify(pages):
    """Assign each page index a (bucket, chapter) target.

    Buckets are output filenames; the special bucket ``"intro.md"`` catches
    the front matter before the first part heading.
    """

    assignment = []
    part = None
    part_prefix = None
    chapter = None
    appendix = None
    seen_parts = set()
    for index, text in enumerate(pages):
        if not text.strip():
            continue
        if _PART_RE.search(text):
            match = _PART_RE.search(text)
            part = PART_TITLES[match.group(0).strip()]
            part_prefix = part[0]
            chapter = None
            appendix = None
            seen_parts.add(part_prefix)
            continue
        appendix_match = _APPENDIX_RE.search(text)
        if appendix_match:
            letter = appendix_match.group(1) or appendix_match.group(2)
            if letter != appendix and "tipo-examen" in seen_parts:
                appendix = letter
                part = None
                part_prefix = None
                chapter = None
                assignment.append((index, APPENDIX_FILES[appendix], None, APPENDIX_TITLES[appendix]))
                continue
        if appendix is not None:
            assignment.append((index, APPENDIX_FILES[appendix], None, APPENDIX_TITLES[appendix]))
            continue
        chapter_match = _CHAPTER_RE.search(text)
        if chapter_match:
            chapter = chapter_match.group(1)
        else:
            header_match = _CHAPTER_HEADER_RE.search(text)
            if header_match:
                chapter = _NAME_TO_CHAPTER[header_match.group(1)]
        if part_prefix is None or chapter is None:
            assignment.append((index, "intro.md", None, "Introducción"))
            continue
        assignment.append(
            (index,
             f"{part_prefix}-{chapter}.md",
             chapter,
             f"Capítulo {chapter} · {CHAPTER_NAMES[chapter]}")
        )
    return assignment


def split_pages(pages):
    """Return {filename: content} for the master cuadernillo page texts."""

    files = {}
    ranges = {}
    titles = {}
    assignment = _classify(pages)
    for index, filename, chapter, title in assignment:
        body = _clean_page(pages[index])
        if not body.strip():
            continue
        files.setdefault(filename, [])
        files[filename].append(body)
        first, last = ranges.get(filename, (index + 1, index + 1))
        ranges[filename] = (min(first, index + 1), max(last, index + 1))
        titles.setdefault(filename, title)
        if chapter is not None:
            titles.setdefault(f"chapter:{filename}", chapter)

    output = {}
    for filename in sorted(files):
        title = titles.get(filename, "Sin clasificar")
        first, last = ranges[filename]
        header = f"# {title}\n\nFuente: cuadernillo \"Ejercicios y respuestas\", páginas {first}–{last} del PDF.\n\n"
        output[filename] = header + "\n\n".join(files[filename]) + "\n"

    categories = {}
    for filename, content in output.items():
        if not filename.startswith("tipo-examen-"):
            continue
        found = sorted({match.group(1).strip() for match in _CATEGORY_RE.finditer(content)})
        if found:
            categories[filename] = found
    output["INDICE.md"] = _index(output, ranges, titles, categories)
    output["funciones-vilcretas.txt"] = _functions(output.get("apendice-b.md", ""))
    return output


def _index(output, ranges, titles, categories):
    lines = [
        "# Índice del cuadernillo Ejercicios y respuestas",
        "",
        "El cuadernillo maestro del curso, dividido en archivos de texto plano.",
        "Cada ejercicio se numera `capítulo.sección.ejercicio` (por ejemplo `3.4.12`)",
        "y ese número es el mismo del libro.",
        "",
        "## Cómo buscar",
        "",
        "- Con grep: números de ejercicio (`1.6.5`), nombres de comandos del curso",
        "  (`Productoria`, `RR`, `PruebaADA`, `CompLimit`...) o palabras distintivas",
        "  de la pregunta. Grep devuelve números de línea: usa read con offset y",
        "  limit para leer solo ese rango; nunca leas un archivo completo.",
        "- Para una pregunta de examen, empiece por `tipo-examen-N.md`, donde N es",
        "  el número de capítulo (por ejemplo, `tipo-examen-3.md` para `cap3`): reproduce",
        "  el estilo del banco real. `complementarios-N.md` trae la solución paso",
        "  a paso. `apendice-b.md` cataloga las funciones VilCretas.",
        "",
        "## Archivos",
        "",
        "| archivo | contenido | páginas del PDF |",
        "|---|---|---|",
    ]
    for filename in sorted(output):
        if filename in {"INDICE.md", "funciones-vilcretas.txt"}:
            continue
        first, last = ranges[filename]
        title = titles.get(filename, "")
        lines.append(f"| {filename} | {title} | {first}–{last} |")
    if categories:
        lines.append("")
        lines.append("## Categorías tipo examen por capítulo")
        for filename in sorted(categories):
            lines.append("")
            chapter = titles.get(f"chapter:{filename}", "")
            label = CHAPTER_NAMES.get(chapter, filename)
            lines.append(f"### {filename} (Capítulo {chapter} · {label})" if chapter else f"### {filename}")
            lines.append("")
            for category in categories[filename]:
                lines.append(f"- {category}")
    return "\n".join(lines) + "\n"


def _functions(apendice_b):
    names = sorted(set(_FUNCTION_ROW_RE.findall(apendice_b)))
    return "".join(name + "\n" for name in names)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf")
    parser.add_argument("outdir")
    args = parser.parse_args(argv)

    from pypdf import PdfReader

    reader = PdfReader(args.pdf)
    pages = [page.extract_text() or "" for page in reader.pages]
    output = split_pages(pages)
    os.makedirs(args.outdir, exist_ok=True)
    for filename, content in output.items():
        with open(os.path.join(args.outdir, filename), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"extract_fuentes: {len(reader.pages)} páginas -> {len(output)} archivos en {args.outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
