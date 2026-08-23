import unittest

from vicre.consultation import ConsultationValidationError, parse_and_validate


class ConsultationResultTests(unittest.TestCase):
    def test_valid_repeated_result_is_normalized_and_keeps_metadata(self):
        output = """
RESPUESTA_TIPO1:
#1: la respuesta

RESPUESTA_TIPO2:
```wl
Table [ {n, RepeatedTiming [ f[n] ][[1]]}, {n, 1, 20, 3}]
ListLinePlot [ data ]
```
PROCEDIMIENTO: timing_repeated
"""

        result = parse_and_validate(output)

        self.assertEqual(result.tipo1, "#1: la respuesta")
        self.assertIn("Table", result.tipo2)
        self.assertNotIn("```", result.tipo2)
        self.assertEqual(result.procedures, ("timing_repeated",))

    def test_valid_repeated_result_allows_plot_label_strings(self):
        output = '''
RESPUESTA_TIPO1:
#1: f
RESPUESTA_TIPO2:
Table[{n, RepeatedTiming[f[n]][[1]]}, {n, 1, 20, 3}]
ListLinePlot[{data1, data2}, PlotLabels -> {"d1", "d2"}]
PROCEDIMIENTO: timing_repeated
'''

        result = parse_and_validate(output)

        self.assertIn('PlotLabels -> {"d1", "d2"}', result.tipo2)

    def test_unclosed_string_is_rejected(self):
        output = '''
RESPUESTA_TIPO1:
#1: f
RESPUESTA_TIPO2:
Table[{n, RepeatedTiming[f[n]][[1]]}, {n, 1, 20, 3}]
ListLinePlot[data, PlotLabel -> "d1]
PROCEDIMIENTO: timing_repeated
'''

        with self.assertRaisesRegex(ConsultationValidationError, "cadena|cerrar"):
            parse_and_validate(output)

    def test_graphica_requires_declared_union_and_numeric_evaluation(self):
        output = """
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
{f[859745621], g[859745621]} // N
PruebaADAGrafica[{f, g}, 200, 1, 20]
PROCEDIMIENTO: numeric_compare, timing_graphica
"""

        result = parse_and_validate(output)

        self.assertEqual(
            result.procedures, ("numeric_compare", "timing_graphica")
        )

    def test_missing_graphica_construct_is_precise(self):
        output = """
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
{f[10], g[10]}
PROCEDIMIENTO: numeric_compare, timing_graphica
"""

        with self.assertRaisesRegex(ConsultationValidationError, "timing_graphica"):
            parse_and_validate(output)

    def test_missing_aggregate_construct_is_precise(self):
        output = """
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
Limit[expr/candidate, n -> Infinity]
PROCEDIMIENTO: asymptotic_product
"""

        with self.assertRaisesRegex(ConsultationValidationError, "Product"):
            parse_and_validate(output)

    def test_valid_product_limit_result_is_paste_ready(self):
        output = """
RESPUESTA_TIPO1:
#4: notación asintótica
RESPUESTA_TIPO2:
Limit[
  Product[term[i], {i, 1, n - 2}]/candidate,
  n -> Infinity
]
PROCEDIMIENTO: asymptotic_product
"""

        result = parse_and_validate(output)

        self.assertIn("Product", result.tipo2)
        self.assertIn("Limit", result.tipo2)
        self.assertNotIn("PROCEDIMIENTO", result.tipo2)

    def test_additional_fence_is_rejected(self):
        output = """
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
```wl
Table[RepeatedTiming[f[n]][[1]], {n, 1, 10}]
```
```
PROCEDIMIENTO: timing_repeated
"""

        with self.assertRaisesRegex(ConsultationValidationError, "fence|código"):
            parse_and_validate(output)

    def test_unknown_procedure_is_rejected(self):
        output = """
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
Sum[term, {i, 1, n}]
PROCEDIMIENTO: made_up
"""

        with self.assertRaisesRegex(ConsultationValidationError, "desconocido|unknown"):
            parse_and_validate(output)

    def test_expected_procedure_cannot_be_omitted(self):
        output = """
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
Table[{n, RepeatedTiming[f[n]][[1]]}, {n, 1, 10}]
ListLinePlot[data]
PROCEDIMIENTO: timing_repeated
"""

        with self.assertRaisesRegex(ConsultationValidationError, "timing_graphica"):
            parse_and_validate(output, expected_procedures=("timing_graphica",))

    def test_preamble_before_first_section_is_rejected(self):
        output = """
Here is the answer:
RESPUESTA_TIPO1:
#1: respuesta
RESPUESTA_TIPO2:
Sum[term, {i, 1, n}]
PROCEDIMIENTO: loop_count
"""

        with self.assertRaisesRegex(ConsultationValidationError, "antes|preamble"):
            parse_and_validate(output)

    def test_construct_words_in_strings_or_assignments_do_not_count(self):
        output = """
RESPUESTA_TIPO1:
#4: respuesta
RESPUESTA_TIPO2:
Print["Product and Limit"];
Sum = 1;
Limit = 2;
PROCEDIMIENTO: asymptotic_product
"""

        with self.assertRaisesRegex(ConsultationValidationError, "Product"):
            parse_and_validate(output)

    def test_unbalanced_wolfram_delimiters_are_rejected(self):
        output = """
RESPUESTA_TIPO1:
#4: respuesta
RESPUESTA_TIPO2:
Limit[Product[f[i], {i, 1, n}, n -> Infinity]
PROCEDIMIENTO: asymptotic_product
"""

        with self.assertRaisesRegex(ConsultationValidationError, "balance|corchete|delimit"):
            parse_and_validate(output)

    def test_numeric_compare_requires_balanced_concrete_function_call(self):
        for code in ("data[[1]]", "f[1"):
            output = f"""
RESPUESTA_TIPO1:
#3: respuesta
RESPUESTA_TIPO2:
{code}
PROCEDIMIENTO: numeric_compare
"""
            with self.subTest(code=code):
                with self.assertRaises(ConsultationValidationError):
                    parse_and_validate(output)

    def test_timing_code_cannot_redefine_pattern_functions(self):
        output = """
RESPUESTA_TIPO1:
#2: respuesta
RESPUESTA_TIPO2:
f[n_] := n + 1
Table[{n, RepeatedTiming[f[n]][[1]]}, {n, 1, 10}]
ListLinePlot[data]
PROCEDIMIENTO: timing_repeated
"""

        with self.assertRaisesRegex(ConsultationValidationError, "redefinir|redefin"):
            parse_and_validate(output)

    def test_timing_code_rejects_equivalent_function_definitions(self):
        for definition in (
            "SetDelayed[f[n_], n + 1]",
            "f = Function[{n}, n + 1]",
        ):
            output = f'''
RESPUESTA_TIPO1:
#2: respuesta
RESPUESTA_TIPO2:
{definition}
Table[{{n, RepeatedTiming[f[n]][[1]]}}, {{n, 1, 10}}]
ListLinePlot[data]
PROCEDIMIENTO: timing_repeated
'''
            with self.subTest(definition=definition):
                with self.assertRaisesRegex(
                    ConsultationValidationError, "redefinir|redefin"
                ):
                    parse_and_validate(output)

    def test_plain_prose_inside_tipo2_is_rejected(self):
        output = '''
RESPUESTA_TIPO1:
#2: respuesta
RESPUESTA_TIPO2:
Primero calculamos los tiempos:
Table[{n, RepeatedTiming[f[n]][[1]]}, {n, 1, 10}]
ListLinePlot[data]
PROCEDIMIENTO: timing_repeated
'''

        with self.assertRaisesRegex(ConsultationValidationError, "prosa"):
            parse_and_validate(output)

    def test_numeric_function_definition_is_not_a_concrete_evaluation(self):
        output = """
RESPUESTA_TIPO1:
#3: respuesta
RESPUESTA_TIPO2:
f[n_] := n + 1
PROCEDIMIENTO: numeric_compare
"""

        with self.assertRaisesRegex(ConsultationValidationError, "evaluación|evaluation"):
            parse_and_validate(output)


if __name__ == "__main__":
    unittest.main()
