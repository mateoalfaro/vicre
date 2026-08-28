import unittest

from vicre.prompt import MAX_REPAIR_PRIOR_CHARS, build_prompt, build_repair_prompt


class PromptTests(unittest.TestCase):
    def test_base_prompt_describes_navigation_and_output_contract(self):
        prompt = build_prompt(())

        self.assertIn("INDICE.md", prompt)
        self.assertIn("tipo-examen-capN.md", prompt)
        self.assertIn("RESPUESTA_TIPO1:", prompt)
        self.assertIn("RESPUESTA_TIPO2:", prompt)
        self.assertIn("PROCEDIMIENTO: capN[, capN...]", prompt)
        for chapter in ("cap1", "cap4", "cap8"):
            self.assertIn(chapter, prompt)
        self.assertNotIn("RUTEO OCR", prompt)

    def test_known_expected_chapters_are_explicitly_required(self):
        prompt = build_prompt(("cap3", "cap8"))

        self.assertIn("cap3, cap8", prompt)
        self.assertIn("obligatorio", prompt)

    def test_repair_prompt_bounds_prior_output_and_notes_truncation(self):
        prompt = build_repair_prompt("falta cap3", "x" * (MAX_REPAIR_PRIOR_CHARS + 500))

        self.assertLess(len(prompt), MAX_REPAIR_PRIOR_CHARS + 2_000)
        self.assertIn("salida anterior truncada", prompt)
        self.assertIn("RESPUESTA_TIPO1:", prompt)
        self.assertIn("PROCEDIMIENTO: capN[, capN...]", prompt)


if __name__ == "__main__":
    unittest.main()
