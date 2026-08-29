"""Parse and validate the result of a Vicre consultation.

The OpenCode process is deliberately kept outside this module.  This is the
pure boundary where an untrusted model response becomes a value that Vicre is
allowed to persist and paste.  Keeping the boundary small also makes the
format and procedure requirements testable without starting a daemon.
"""

from dataclasses import dataclass
import re
from typing import Iterable, Sequence


M1 = "RESPUESTA_TIPO1"
M2 = "RESPUESTA_TIPO2"


class ConsultationValidationError(ValueError):
    """A model response was not safe or complete enough to persist."""

    def __init__(self, message: str, *, errors: Iterable[str] = ()):
        super().__init__(message)
        self.errors = tuple(errors) or (message,)


# Short alias for callers that prefer the general name at this seam.
ValidationError = ConsultationValidationError


@dataclass(frozen=True)
class ConsultationResult:
    """The normalized, validated material returned by a consultation."""

    tipo1: str
    tipo2: str
    procedures: tuple[str, ...]

    @property
    def procedure_ids(self) -> tuple[str, ...]:
        """An explicit alias for consumers that use the metadata vocabulary."""

        return self.procedures

    @property
    def procedure_id(self):
        """Singular metadata alias, or ``None`` for a declared union."""

        return self.procedures[0] if len(self.procedures) == 1 else None

    @property
    def procedure(self):
        """The old singular shape for one procedure, or all IDs for a union."""

        if len(self.procedures) == 1:
            return self.procedures[0]
        return self.procedures

    @property
    def metadata(self) -> dict[str, object]:
        """Serializable procedure metadata for state/logging integrations."""

        return {"procedures": self.procedures}

    def __iter__(self):
        """Allow legacy ``tipo1, tipo2 = parse_output(...)`` callers."""

        yield self.tipo1
        yield self.tipo2


# The chapter IDs are the routing vocabulary of the master cuadernillo.  The
# model receives the navigation material in fuentes; this table is the
# executable policy at the result seam.
CHAPTERS = {
    "cap1": "Recursividad",
    "cap2": "Relaciones de recurrencia",
    "cap3": "Análisis de algoritmos",
    "cap4": "Relaciones binarias",
    "cap5": "Teoría de grafos",
    "cap6": "Teoría de árboles",
    "cap7": "Máquinas de estado finito y autómatas",
    "cap8": "Lenguajes y gramáticas",
}

_SECTION_RE = re.compile(
    r"^[ \t]*(RESPUESTA_TIPO[12])[ \t]*:[ \t]*", re.IGNORECASE | re.MULTILINE
)
_PROCEDURE_RE = re.compile(
    r"^[ \t]*PROCEDIMIENTO[ \t]*:[ \t]*([^\r\n]*)[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
_CODE_FENCE_RE = re.compile(
    r"\A[ \t]*```(?:wl|mathematica)?[ \t]*\r?\n"
    r"([\s\S]*?)\r?\n[ \t]*```[ \t]*\Z",
    re.IGNORECASE,
)
_PROSE_PREFIX_RE = re.compile(
    r"^(?:here(?: is|\'s)?(?: the)? code|the code|codigo|código|"
    r"explicaci[oó]n|explanation|verificaci[oó]n|verification)\b",
    re.IGNORECASE,
)
_PLAIN_PROSE_RE = re.compile(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,}"
    r"(?:[ \t]+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,}){2,}[ \t]*[:.]?$"
)
_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$", re.IGNORECASE)
_CALL_RE = re.compile(r"(?<![A-Za-z0-9_$])([A-Za-z$][A-Za-z0-9_$]*)[ \t]*\[")


def _section_positions(output: str) -> tuple[re.Match[str], re.Match[str]]:
    matches = list(_SECTION_RE.finditer(output))
    if not matches:
        raise ConsultationValidationError(
            f"no se encontró {M1} ni {M2}"
        )

    first = [match for match in matches if match.group(1).upper() == M1]
    second = [match for match in matches if match.group(1).upper() == M2]
    if not first:
        raise ConsultationValidationError(f"no se encontró {M1}")
    if not second:
        raise ConsultationValidationError(f"no se encontró {M2}")
    if len(first) > 1:
        raise ConsultationValidationError(f"se encontró {M1} más de una vez")
    if len(second) > 1:
        raise ConsultationValidationError(f"se encontró {M2} más de una vez")
    if first[0].start() > second[0].start():
        raise ConsultationValidationError("RESPUESTA_TIPO2 aparece antes de RESPUESTA_TIPO1")
    return first[0], second[0]


def _procedure_ids(marker_value: str) -> tuple[str, ...]:
    raw_ids = [part.strip() for part in marker_value.split(",")]
    if not marker_value.strip() or any(not part for part in raw_ids):
        raise ConsultationValidationError(
            "PROCEDIMIENTO debe declarar uno o más IDs separados por comas"
        )

    result = []
    for raw_id in raw_ids:
        procedure_id = raw_id.casefold()
        if not _ID_RE.fullmatch(raw_id):
            raise ConsultationValidationError(
                f"ID de capítulo inválido: {raw_id!r}"
            )
        if procedure_id not in CHAPTERS:
            known = ", ".join(CHAPTERS)
            raise ConsultationValidationError(
                f"capítulo desconocido: {raw_id}; IDs válidos: {known}"
            )
        if procedure_id not in result:
            result.append(procedure_id)
    return tuple(result)


def _strip_one_code_fence(tipo2: str) -> str:
    value = tipo2.strip()
    match = _CODE_FENCE_RE.fullmatch(value)
    if match:
        value = match.group(1).strip()
    if "```" in value:
        raise ConsultationValidationError(
            "RESPUESTA_TIPO2 contiene fences de código adicionales"
        )
    return value


def _sanitize_wolfram(source: str) -> str:
    """Blank comments and strings while preserving structural delimiters."""

    result = []
    depth = 0
    in_string = False
    escaped = False
    index = 0
    while index < len(source):
        pair = source[index:index + 2]
        char = source[index]
        if depth:
            if pair == "(*":
                depth += 1
                index += 2
            elif pair == "*)":
                depth -= 1
                index += 2
            else:
                result.append("\n" if char == "\n" else " ")
                index += 1
            continue
        if in_string:
            result.append("\n" if char == "\n" else " ")
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if pair == "(*":
            depth = 1
            result.extend((" ", " "))
            index += 2
        else:
            if char == '"':
                in_string = True
                result.append(" ")
            else:
                result.append(char)
            index += 1
    if depth:
        raise ConsultationValidationError(
            "RESPUESTA_TIPO2 contiene un comentario Wolfram sin cerrar"
        )
    if in_string:
        raise ConsultationValidationError(
            "RESPUESTA_TIPO2 contiene una cadena Wolfram sin cerrar"
        )
    return "".join(result)


def _without_wolfram_comments(source: str) -> str:
    """Compatibility alias for the old internal helper."""

    return _sanitize_wolfram(source)


def _validate_balanced(code: str) -> None:
    sanitized = _sanitize_wolfram(code)
    expected = {"[": "]", "{": "}", "(": ")"}
    stack = []
    for char in sanitized:
        if char in expected:
            stack.append(expected[char])
        elif char in expected.values():
            if not stack or stack.pop() != char:
                raise ConsultationValidationError(
                    "RESPUESTA_TIPO2 contiene delimitadores Wolfram desbalanceados"
                )
    if stack:
        raise ConsultationValidationError(
            "RESPUESTA_TIPO2 contiene delimitadores Wolfram desbalanceados"
        )


def _definition_records(code: str):
    """Yield (name, body, is_definition) for balanced Wolfram calls."""

    sanitized = _sanitize_wolfram(code)
    for match in _CALL_RE.finditer(sanitized):
        opening = match.end() - 1
        depth = 0
        in_string = False
        escaped = False
        closing = None
        for index in range(opening, len(sanitized)):
            char = sanitized[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    closing = index
                    break
        if closing is None:
            continue
        is_definition = re.match(
            r"\s*(?::=|=)", sanitized[closing + 1:]
        ) is not None
        yield match.group(1), sanitized[opening + 1:closing], is_definition


def _redefined_pattern_functions(code: str) -> tuple[str, ...]:
    names = []
    for name, body, is_definition in _definition_records(code):
        if is_definition and "_" in body:
            names.append(name)
        if name.casefold() in {"set", "setdelayed"} and "_" in body:
            target = re.match(r"\s*([A-Za-z$][A-Za-z0-9_$]*)", body)
            names.append(target.group(1) if target else name)
    sanitized = _sanitize_wolfram(code)
    names.extend(
        match.group(1)
        for match in re.finditer(
            r"(?<![A-Za-z0-9_$])([A-Za-z$][A-Za-z0-9_$]*)\s*=\s*Function\s*\[",
            sanitized,
            re.IGNORECASE,
        )
    )
    return tuple(dict.fromkeys(names))


def _validate_code(tipo2: str, procedures: tuple[str, ...]) -> None:
    if not tipo2:
        raise ConsultationValidationError("respuesta tipo 2 vacía")

    _validate_balanced(tipo2)

    for line in tipo2.splitlines():
        stripped = line.strip()
        if _PROSE_PREFIX_RE.match(stripped) or _PLAIN_PROSE_RE.fullmatch(stripped):
            raise ConsultationValidationError(
                "RESPUESTA_TIPO2 debe contener Wolfram sin prosa"
            )


def _expected_ids(expected_procedures: Sequence[str] | str | None) -> tuple[str, ...]:
    if not expected_procedures:
        return ()
    if isinstance(expected_procedures, str):
        values = expected_procedures
    else:
        values = ",".join(expected_procedures)
    return _procedure_ids(values)


def _validate_protected(tipo2: str, protected_names) -> None:
    if not protected_names:
        return
    protected = {str(name).casefold() for name in protected_names}
    redefined = [
        name
        for name in _redefined_pattern_functions(tipo2)
        if name.casefold() in protected
    ]
    if redefined:
        raise ConsultationValidationError(
            "RESPUESTA_TIPO2 redefine una función del curso: "
            + ", ".join(redefined)
        )


def parse_and_validate(
    output: str,
    expected_procedures: Sequence[str] | str | None = None,
    protected_names: Sequence[str] | str | None = None,
) -> ConsultationResult:
    """Parse, normalize, and validate one complete model response.

    The returned ``tipo2`` is paste-ready: one outer Wolfram fence is removed
    and the final ``PROCEDIMIENTO`` marker is never included.  Any narration
    before the first ``RESPUESTA_TIPO1`` header is ignored.  A duplicated or
    misplaced section, unknown chapter, leftover fence, expected chapter left
    out, or a redefinition of a protected course function raises
    :class:`ConsultationValidationError` with a focused message.
    """

    if isinstance(protected_names, str):
        protected_names = [protected_names]
    if not isinstance(output, str):
        raise ConsultationValidationError("la respuesta de OpenCode no es texto")
    output = output.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    if not _SECTION_RE.search(output):
        raise ConsultationValidationError(f"no se encontró {M1} ni {M2}")
    # Agent narration before the first section header (introductions, notes
    # about the consulted files) is tolerated and ignored.
    output = output[_SECTION_RE.search(output).start():]
    first, second = _section_positions(output)

    marker_matches = list(_PROCEDURE_RE.finditer(output))
    if not marker_matches:
        raise ConsultationValidationError(
            "no se encontró el marcador final PROCEDIMIENTO con ID"
        )
    if len(marker_matches) > 1:
        raise ConsultationValidationError(
            "PROCEDIMIENTO debe aparecer exactamente una vez al final"
        )
    marker = marker_matches[0]
    if marker.start() <= second.end():
        raise ConsultationValidationError(
            "PROCEDIMIENTO debe aparecer después de RESPUESTA_TIPO2"
        )
    if output[marker.end():].strip():
        raise ConsultationValidationError(
            "PROCEDIMIENTO debe ser el marcador final de la respuesta"
        )

    tipo1 = output[first.end():second.start()].strip()
    if not tipo1:
        raise ConsultationValidationError("respuesta tipo 1 vacía")
    procedures = _procedure_ids(marker.group(1))
    expected = _expected_ids(expected_procedures)
    missing_expected = tuple(
        procedure_id for procedure_id in expected if procedure_id not in procedures
    )
    if missing_expected:
        raise ConsultationValidationError(
            "faltan capítulos esperados: " + ", ".join(missing_expected),
            errors=tuple(
                f"falta capítulo esperado: {procedure_id}"
                for procedure_id in missing_expected
            ),
        )
    tipo2 = _strip_one_code_fence(output[second.end():marker.start()])
    _validate_code(tipo2, procedures)
    _validate_protected(tipo2, protected_names)
    return ConsultationResult(tipo1=tipo1, tipo2=tipo2, procedures=procedures)


def parse_output(
    output: str,
    expected_procedures: Sequence[str] | str | None = None,
) -> ConsultationResult:
    """Compatibility/public alias for the consultation-result seam."""

    return parse_and_validate(output, expected_procedures=expected_procedures)
