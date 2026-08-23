import unittest

from vicre.prompt import MAX_REPAIR_PRIOR_CHARS, build_prompt, build_repair_prompt


class PromptTests(unittest.TestCase):
    def test_known_expected_ids_are_explicitly_required(self):
        prompt = build_prompt(("numeric_compare", "timing_graphica"))

        self.assertIn("numeric_compare, timing_graphica", prompt)
        self.assertIn("obligatorio", prompt)

    def test_repair_prompt_bounds_prior_output_and_notes_truncation(self):
        prompt = build_repair_prompt("falta Product", "x" * (MAX_REPAIR_PRIOR_CHARS + 500))

        self.assertLess(len(prompt), MAX_REPAIR_PRIOR_CHARS + 2_000)
        self.assertIn("salida anterior truncada", prompt)


if __name__ == "__main__":
    unittest.main()
