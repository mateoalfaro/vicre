import unittest

from vicre.routing import infer_expected_procedures, ocr_image


class NormalizeTests(unittest.TestCase):
    def test_empty_text_has_no_hints(self):
        self.assertEqual(infer_expected_procedures(""), ())
        self.assertEqual(infer_expected_procedures("   \n  "), ())
        self.assertEqual(infer_expected_procedures(None), ())

    def test_noise_text_has_no_hints(self):
        self.assertEqual(infer_expected_procedures("valor 23 igual a siete"), ())


class ChapterRoutingTests(unittest.TestCase):
    def test_recursion_keywords_route_to_cap1(self):
        text = "Escriba un programa recursivo de pila para la sucesión de Fibonacci"
        self.assertEqual(infer_expected_procedures(text), ("cap1",))

    def test_recurrence_keywords_route_to_cap2(self):
        text = "Resuelva la relación de recurrencia homogénea con la ecuación característica"
        self.assertEqual(infer_expected_procedures(text), ("cap2",))

    def test_algorithm_keywords_route_to_cap3(self):
        self.assertEqual(infer_expected_procedures("O grande del algoritmo"), ("cap3",))
        self.assertEqual(
            infer_expected_procedures("use RepeatedTiming y ListLinePlot"), ("cap3",)
        )
        self.assertEqual(infer_expected_procedures("PruebaADA"), ("cap3",))

    def test_graph_keywords_route_to_cap5(self):
        self.assertEqual(
            infer_expected_procedures("circuito de Euler en la teoría de grafos"),
            ("cap5",),
        )

    def test_tree_keywords_route_to_cap6(self):
        self.assertEqual(
            infer_expected_procedures("código de Huffman del árbol"), ("cap6",)
        )

    def test_automata_keywords_route_to_cap7(self):
        self.assertEqual(
            infer_expected_procedures("Autómatas: hileras aceptadas por un AFD"),
            ("cap7",),
        )

    def test_grammar_keywords_route_to_cap8(self):
        self.assertEqual(
            infer_expected_procedures("gramática libre de contexto en BNF"), ("cap8",)
        )

    def test_several_chapters_keep_vocabulary_order(self):
        text = "el árbol de Huffman y el circuito del grafo"
        self.assertEqual(infer_expected_procedures(text), ("cap5", "cap6"))

    def test_camelcase_commands_survive_normalization(self):
        self.assertEqual(
            infer_expected_procedures("MetodoRRHL y FindRRHL"), ("cap2",)
        )


class OcrImageTests(unittest.TestCase):
    def test_missing_binary_returns_empty_text(self):
        self.assertEqual(ocr_image("/nonexistent/photo.png"), "")


if __name__ == "__main__":
    unittest.main()
