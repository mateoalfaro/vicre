"""Prompts for the small, deterministic Vicre consultation agent."""


PROMPT = """La imagen adjunta contiene una o más preguntas de un examen de matemáticas discretas que se resuelven con Wolfram Mathematica y la biblioteca de Vilcretas. Consulta únicamente las tarjetas Markdown compactas de fuentes/ que correspondan a la captura. No busques ni inventes claves, rúbricas, respuestas de evaluación o material fuera de esas tarjetas.

Identifica cada inciso visible y responde EXACTAMENTE con estas secciones y en este orden. No escribas texto antes, entre ni después salvo el marcador PROCEDIMIENTO final:

RESPUESTA_TIPO1:
Respuestas directas a cada pregunta o parte vacía de la foto, numeradas como aparecen (por ejemplo, #1: valor, #2: valor). Sin explicaciones ni desarrollo.

RESPUESTA_TIPO2:
Código Wolfram Mathematica que compruebe RESPUESTA_TIPO1 cuando corresponda. Debe ser código Wolfram crudo listo para pegar: sin fences Markdown, sin prosa, sin encabezados y sin comentarios explicativos. Copia los operadores exactamente como aparecen en la tarjeta elegida y usa la forma del procedimiento que pide la captura. En los procedimientos de tiempos llama a funciones ya definidas por el curso: no incluyas redefiniciones como `f[n_] := ...`.

PROCEDIMIENTO: id[, id...]
En la última línea declara uno o más IDs de tarjetas separados por comas, usando solamente: timing_repeated, timing_graphica, asymptotic_sum, asymptotic_product, comp_limit, loop_count, numeric_compare. Declara la unión completa de procedimientos necesarios para RESPUESTA_TIPO2. El marcador es metadato de Vicre y nunca forma parte de RESPUESTA_TIPO2.

Diferencia los experimentos: timing_repeated requiere Table + RepeatedTiming + ListLinePlot; timing_graphica requiere PruebaADAGrafica. Si la captura pide ambos, declara y ejecuta ambos. Para una comparación numérica concreta incluye una llamada Wolfram con la entrada exacta, además de cualquier experimento solicitado."""


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
        "\n\nRUTEO OCR (obligatorio): la captura coincide con estos IDs de "
        "procedimiento: "
        + ", ".join(ids)
        + ". Declara todos en la línea PROCEDIMIENTO y usa todos sus "
        "constructos; no omitas ni sustituyas ninguno."
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

Corrige únicamente el formato o los procedimientos faltantes usando la imagen adjunta y las tarjetas de fuentes/. Conserva las respuestas directas cuando sean válidas. Devuelve EXACTAMENTE las tres secciones siguientes, sin texto adicional:

RESPUESTA_TIPO1:
(respuestas directas numeradas)

RESPUESTA_TIPO2:
(Wolfram crudo listo para pegar, sin fences ni prosa; incluye todos los constructos requeridos por los IDs declarados)

PROCEDIMIENTO: id[, id...]
(última línea, con los IDs válidos y necesarios; nunca lo incluyas dentro de RESPUESTA_TIPO2)

RESPUESTA ANTERIOR PARA CORREGIR:
{prior_output}"""
