"""Prompts for the small, deterministic Vicre consultation agent."""


PROMPT = """La imagen adjunta contiene una o más preguntas de un examen de matemáticas discretas que se resuelven con Wolfram Mathematica y la biblioteca de Vilcretas.

En fuentes/ está el cuadernillo maestro del curso ("Ejercicios y respuestas") dividido en archivos de texto: lee primero fuentes/INDICE.md; luego navega según cada pregunta. Para una pregunta de examen empieza por el archivo tipo-examen-capN.md de su capítulo (reproduce el estilo del banco real) y consulta también complementarios-capN.md (resueltos paso a paso). Localiza con grep los ejercicios resueltos análogos: números capítulo.sección.ejercicio (por ejemplo 3.4.12), nombres de comandos del curso (Productoria, RR, PruebaADA, CompLimit...) o palabras distintivas de la pregunta, y lee solo esas secciones. apendice-b.md cataloga las funciones de VilCretas. No inventes material fuera del cuadernillo.

Resuelve imitando EXACTAMENTE el procedimiento y la sintaxis Wolfram de esos ejercicios. Las funciones de VilCretas ya están cargadas: llámalas tal cual; nunca las redefinas con patrones como Productoria[x_] := ... .

Identifica cada inciso visible y responde EXACTAMENTE con estas secciones y en este orden. No escribas texto antes, entre ni después salvo el marcador PROCEDIMIENTO final:

RESPUESTA_TIPO1:
Respuestas directas a cada pregunta o parte vacía de la foto, numeradas como aparecen (por ejemplo, #1: valor, #2: valor). Sin explicaciones ni desarrollo.

RESPUESTA_TIPO2:
Código Wolfram Mathematica que compruebe RESPUESTA_TIPO1 cuando corresponda. Debe ser código Wolfram crudo listo para pegar: sin fences Markdown, sin prosa, sin encabezados y sin comentarios explicativos. Usa los comandos del curso tal como aparecen en el cuadernillo y no redefinas funciones ya definidas.

PROCEDIMIENTO: capN[, capN...]
En la última línea declara los capítulos del cuadernillo que consultaste, separados por comas, usando solamente: cap1 (Recursividad), cap2 (Relaciones de recurrencia), cap3 (Análisis de algoritmos), cap4 (Relaciones binarias), cap5 (Teoría de grafos), cap6 (Teoría de árboles), cap7 (Máquinas de estado finito y autómatas), cap8 (Lenguajes y gramáticas). El marcador es metadato de Vicre y nunca forma parte de RESPUESTA_TIPO2."""


MAX_REPAIR_PRIOR_CHARS = 12_000


def _ids(expected_procedures):
    if not expected_procedures:
        return ()
    if isinstance(expected_procedures, str):
        values = expected_procedures.split(",")
    else:
        values = expected_procedures
    return tuple(str(value).strip() for value in values if str(value).strip())


def _expected_hint(expected_procedures) -> str:
    ids = _ids(expected_procedures)
    if not ids:
        return ""
    return (
        "\n\nRUTEO OCR (obligatorio): la captura corresponde a estos capítulos: "
        + ", ".join(ids)
        + ". Declara todos en la línea PROCEDIMIENTO y resuélvelos con el "
        "material de esos capítulos; no omitas ninguno."
    )


def build_prompt(expected_procedures=()):
    return PROMPT + _expected_hint(expected_procedures)


def build_repair_prompt(
    validation_error: str,
    prior_output: str,
    expected_procedures=(),
) -> str:
    """Build one focused repair request without asking the model to re-solve."""

    prior_output = str(prior_output)
    if len(prior_output) > MAX_REPAIR_PRIOR_CHARS:
        prior_output = (
            prior_output[:MAX_REPAIR_PRIOR_CHARS]
            + "\n...[salida anterior truncada a "
            + str(MAX_REPAIR_PRIOR_CHARS)
            + " caracteres]"
        )

    return f"""La respuesta anterior no pasó la validación de Vicre.

ERROR DE VALIDACIÓN:
{validation_error}

{_expected_hint(expected_procedures).lstrip()}

Corrige únicamente el formato o los capítulos faltantes usando la imagen adjunta y el cuadernillo de fuentes/. Conserva las respuestas directas cuando sean válidas. Devuelve EXACTAMENTE las tres secciones siguientes, sin texto adicional:

RESPUESTA_TIPO1:
(respuestas directas numeradas)

RESPUESTA_TIPO2:
(Wolfram crudo listo para pegar, sin fences ni prosa; nunca redefinas funciones de VilCretas)

PROCEDIMIENTO: capN[, capN...]
(última línea, con los IDs de capítulo válidos y necesarios; nunca lo incluyas dentro de RESPUESTA_TIPO2)

RESPUESTA ANTERIOR PARA CORREGIR:
{prior_output}"""
