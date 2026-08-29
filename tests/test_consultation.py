import unittest

from vicre import consultation
from vicre.consultation import (
    ConsultationValidationError,
    parse_and_validate,
    parse_output,
)


def _output(tipo2="Productoria[{2, n, 1 + 2/i}, 5]", procedures="cap1"):
    return (
        "RESPUESTA_TIPO1:\n"
        "#1: 7\n"
        "RESPUESTA_TIPO2:\n"
        f"{tipo2}\n"
        f"PROCEDIMIENTO: {procedures}\n"
    )


class ParseTests(unittest.TestCase):
    def test_valid_response_round_trips(self):
        result = parse_and_validate(_output())

        self.assertEqual(result.tipo1, "#1: 7")
        self.assertEqual(result.tipo2, "Productoria[{2, n, 1 + 2/i}, 5]")
        self.assertEqual(result.procedures, ("cap1",))
        self.assertEqual(result.procedure_ids, ("cap1",))
        self.assertEqual(result.metadata, {"procedures": ("cap1",)})

    def test_outer_fence_is_removed(self):
        fenced = _output(tipo2="```wl\nRR[{2, 3}, {1, 2}, n]\n```")
        result = parse_and_validate(fenced)

        self.assertEqual(result.tipo2, "RR[{2, 3}, {1, 2}, n]")

    def test_iterates_legacy_pair(self):
        tipo1, tipo2 = parse_and_validate(_output())
        self.assertEqual(tipo1, "#1: 7")
        self.assertEqual(tipo2, "Productoria[{2, n, 1 + 2/i}, 5]")

    def test_union_of_chapters_is_normalized_and_deduplicated(self):
        result = parse_and_validate(_output(procedures="Cap5, cap5, cap6"))

        self.assertEqual(result.procedures, ("cap5", "cap6"))
        self.assertIsNone(result.procedure_id)


class SectionShapeTests(unittest.TestCase):
    def test_missing_sections(self):
        for broken in ("", "hola", "RESPUESTA_TIPO1:\n#1: 2\nPROCEDIMIENTO: cap1"):
            with self.assertRaises(ConsultationValidationError):
                parse_and_validate(broken)

    def test_only_tipo1_marker_is_required(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate("RESPUESTA_TIPO1:\n#1: 2\nRESPUESTA_TIPO2:\n1\n")

    def test_narration_before_tipo1_is_ignored(self):
        narrated = (
            "He revisado el índice del cuadernillo y localicé el ejercicio análogo.\n"
            + _output()
        )
        result = parse_and_validate(narrated)

        self.assertEqual(result.tipo1, "#1: 7")
        self.assertEqual(result.procedures, ("cap1",))

    def test_multiline_narration_is_ignored(self):
        narrated = "Nota:\n\nEl capítulo consultado es cap1.\n\n" + _output()
        result = parse_and_validate(narrated)

        self.assertEqual(result.tipo1, "#1: 7")

    def test_narration_without_marker_line_is_never_a_false_header(self):
        narrated = (
            "Primero reviso fuentes; RESPUESTA_TIPO1 viene abajo.\n" + _output()
        )
        result = parse_and_validate(narrated)

        self.assertEqual(result.tipo1, "#1: 7")

    def test_tipo2_before_tipo1_is_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(
                "RESPUESTA_TIPO2:\n1\nRESPUESTA_TIPO1:\n#1: 2\nPROCEDIMIENTO: cap1\n"
            )

    def test_empty_tipo1_is_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(
                "RESPUESTA_TIPO1:\nRESPUESTA_TIPO2:\n1\nPROCEDIMIENTO: cap1\n"
            )

    def test_non_text_output_is_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(b"bytes")


class MarkerTests(unittest.TestCase):
    def test_missing_marker(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate("RESPUESTA_TIPO1:\n#1: 2\nRESPUESTA_TIPO2:\n1\n")

    def test_duplicated_marker(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(_output() + "PROCEDIMIENTO: cap2\n")

    def test_marker_before_tipo2(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(
                "RESPUESTA_TIPO1:\n#1: 2\nPROCEDIMIENTO: cap1\nRESPUESTA_TIPO2:\n1\n"
            )

    def test_trailing_text_after_marker(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(_output() + "un saludo")

    def test_unknown_chapter(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(_output(procedures="timing_repeated"))

    def test_invalid_chapter_id(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(_output(procedures="3 recursividad"))

    def test_expected_chapters_are_enforced(self):
        with self.assertRaises(ConsultationValidationError) as ctx:
            parse_and_validate(_output(procedures="cap1"), expected_procedures="cap1,cap3")

        self.assertIn("faltan capítulos esperados: cap3", str(ctx.exception))


class CodeTests(unittest.TestCase):
    def test_empty_tipo2(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(
                "RESPUESTA_TIPO1:\n#1: 2\nRESPUESTA_TIPO2:\nPROCEDIMIENTO: cap1\n"
            )

    def test_prose_is_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(_output(tipo2="Aquí está el código que pidió"))

    def test_leftover_inner_fence_is_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(
                _output(tipo2="```\n```wl\nRR[{2, 3}, {1, 2}, n]\n```\n```")
            )

    def test_unbalanced_delimiters_are_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(_output(tipo2="Sum[i, {i, 1, n}"))

    def test_unclosed_wolfram_comment_is_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(_output(tipo2="(* sin cerrar\nRR[{2, 3}, {1, 2}, n]"))

    def test_unclosed_wolfram_string_is_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(_output(tipo2='PlotLabel -> "abierto'))


class ProtectedNameTests(unittest.TestCase):
    def test_redefining_a_course_function_is_rejected(self):
        with self.assertRaises(ConsultationValidationError) as ctx:
            parse_and_validate(
                _output(tipo2="Productoria[x_] := If[x == 1, 1, x*Productoria[x - 1]]"),
                protected_names=("Productoria", "RR"),
            )

        self.assertIn("redefine una función del curso: Productoria", str(ctx.exception))

    def test_set_style_redefinition_is_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(
                _output(tipo2="Sum[x, {x, 1, 10}]; Set[Factoriales[n_], n]"),
                protected_names=("Factoriales",),
            )

    def test_function_literal_redefinition_is_rejected(self):
        with self.assertRaises(ConsultationValidationError):
            parse_and_validate(
                _output(tipo2="CompLimit = Function[{n}, n + 1]; CompLimit[3]"),
                protected_names=("CompLimit",),
            )

    def test_definitions_of_other_names_are_allowed(self):
        result = parse_and_validate(
            _output(
                tipo2=(
                    "Lucas[n_] := If[n == 1, 1, If[n == 2, 3, Lucas[n - 1] + Lucas[n - 2]]];\n"
                    "Lucas[8]"
                )
            ),
            protected_names=("Productoria", "Factoriales"),
        )

        self.assertIn("Lucas[8]", result.tipo2)

    def test_no_protected_names_disables_the_check(self):
        result = parse_and_validate(
            _output(tipo2="Productoria[x_] := x"),
        )

        self.assertEqual(result.tipo2, "Productoria[x_] := x")


class CompatibilityTests(unittest.TestCase):
    def test_parse_output_alias(self):
        result = parse_output(_output(), expected_procedures=("cap1",))

        self.assertEqual(result.procedures, ("cap1",))

    def test_validation_error_carries_error_list(self):
        try:
            parse_and_validate(_output(procedures="cap1"), expected_procedures=("cap4",))
        except ConsultationValidationError as error:
            self.assertIn("falta capítulo esperado: cap4", error.errors)
        else:
            self.fail("expected ConsultationValidationError")

    def test_module_exports_chapter_vocabulary(self):
        self.assertEqual(
            set(consultation.CHAPTERS),
            {f"cap{n}" for n in range(1, 9)},
        )


if __name__ == "__main__":
    unittest.main()
