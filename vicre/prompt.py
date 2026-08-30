"""Prompts for the small, deterministic Vicre consultation agent."""


# The prompt is sent as a single user message to `agy -p`; there is no
# separate agent system prompt, so every behavioral rule lives here.
PROMPT_TEMPLATE = """{image_reference} una o más preguntas de un examen de matemáticas discretas que se resuelven con Wolfram Mathematica y la biblioteca de Vilcretas.

En fuentes/ está el cuadernillo maestro del curso ("Ejercicios y respuestas") dividido en archivos de texto: lee primero fuentes/INDICE.md; luego navega según cada pregunta. Para una pregunta de examen empieza por el archivo tipo-examen-capN.md de su capítulo (reproduce el estilo del banco real) y consulta también complementarios-capN.md (resueltos paso a paso). Localiza con grep los ejercicios resueltos análogos: números capítulo.sección.ejercicio (por ejemplo 3.4.12), nombres de comandos del curso (Productoria, RR, PruebaADA, CompLimit...) o palabras distintivas de la pregunta. Grep devuelve números de línea: usa read con offset/limit sobre ese rango, nunca leas archivos completos de una vez. apendice-b.md cataloga las funciones de VilCretas. No inventes material fuera del cuadernillo.

Resuelve imitando EXACTAMENTE el procedimiento y la sintaxis Wolfram de esos ejercicios. Las funciones de VilCretas ya están cargadas: llámalas tal cual; nunca las redefinas con patrones como Productoria[x_] := ... . Administra tus pasos: si no localizas el ejercicio exacto, responde de todos modos con las tres secciones; nunca entregues un resumen del trabajo. No uses subagentes ni ejecutes comandos de shell: navega fuentes/ únicamente con grep y read, y responde directamente tú.

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


def image_reference(photo: str) -> str:
    """The Spanish phrase that tells the model where the screenshot lives.

    agy (the Gemini CLI) has no flag to attach a file to a `-p` prompt, so
    the photo is referenced by an absolute path inside the workspace and the
    model reads it with its own tools (exactly like fuentes/). This keeps the
    prompt modality-agnostic while still anchoring every sentence in the
    image, as the previous "--f photo" flow did.
    """

    return (
        f"La imagen en {photo} contiene"
        if photo
        else "El siguiente texto OCR de una captura de pantalla contiene"
    )


def build_prompt(expected_procedures=(), photo: str = ""):
    return (
        PROMPT_TEMPLATE.format(image_reference=image_reference(photo))
        + _expected_hint(expected_procedures)
    )


def build_repair_prompt(
    validation_error: str,
    prior_output: str,
    expected_procedures=(),
    photo: str = "",
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

Corrige únicamente el formato o los capítulos faltantes usando la imagen adjunta y el cuadernillo de fuentes/. {image_reference(photo)} la(s) respuesta(s). Conserva las respuestas directas cuando sean válidas. Devuelve EXACTAMENTE las tres secciones siguientes, sin texto adicional:

RESPUESTA_TIPO1:
(respuestas directas numeradas)

RESPUESTA_TIPO2:
(Wolfram crudo listo para pegar, sin fences ni prosa; nunca redefinas funciones de VilCretas)

PROCEDIMIENTO: capN[, capN...]
(última línea, con los IDs de capítulo válidos y necesarios; nunca lo incluyas dentro de RESPUESTA_TIPO2)

RESPUESTA ANTERIOR PARA CORREGIR:
{prior_output}"""
