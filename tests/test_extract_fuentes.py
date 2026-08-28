import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from extract_fuentes import split_pages


PAGE_COVER = "CUADERNILLO DE EJERCICIOS\nEjercicios y respuestas\nEnrique Vílchez\n"
PAGE_TOC = (
    "Índice Ejercicios y respuestas\n"
    "Capítulo 1. Recursividad . . . 4\n"
    "Apéndice A. Los recursos del curso . . . 440\n"
    "i\n"
)
PAGE_PART1 = "PRIMERA PARTE\nLos ejercicios\n"
PAGE_CAP1_OPENER = (
    "Recursividad Ejercicios y respuestas\n"
    "CAPÍTULO 1\n"
    "Recursividad\n"
    "1.5 Ejercicios\n"
    "1.5.1 ¿Qué ocurre con la función recursiva?\n"
)
PAGE_CAP1_BODY = (
    "Recursividad Ejercicios y respuestas\n"
    "Genere un programa recursivo de pila:\n"
    "7\n"
    "1.5.2 segundo ejercicio\n"
)
PAGE_CAP2 = (
    "Relaciones de recurrencia Ejercicios y respuestas\n"
    "CAPÍTULO 2\n"
    "Relaciones de recurrencia\n"
    "2.3.1 primera recurrencia\n"
)
PAGE_PART2 = "SEGUNDA PARTE\nLas respuestas\n"
PAGE_RESP1 = (
    "Recursividad Ejercicios y respuestas\n"
    "RESPUESTAS • SECCIÓN 1.5\n"
    "1.5.1 In[ ] :=\n"
)
PAGE_PART3 = "TERCERA PARTE\nEjercicios complementarios, resueltos\n"
PAGE_COMP1 = (
    "Recursividad Ejercicios y respuestas\n"
    "1.6.5 (★★) A MANO La sucesión de Lucas\n"
    "SOLUCIÓN In[ ] :=\n"
)
PAGE_PART4 = "CUARTA PARTE\nPreguntas tipo examen\n"
PAGE_TIPO1 = (
    "Recursividad Ejercicios y respuestas\n"
    "CAPÍTULO 1 • PREGUNTAS TIPO EXAMEN\n"
    "Recursividad\n"
    "1.7.4 (★★★) TIPO EXAMEN A MANO\n"
    "Categoría del banco:3-Rec. Prog. de productorias con Rec. de pila\n"
)
PAGE_TIPO2 = (
    "Recursividad Ejercicios y respuestas\n"
    "1.7.6 (★★) TIPO EXAMEN VilCretas\n"
    "Categoría del banco:5-Rec. Prog. de cola\n"
)
PAGE_APEX_A = "APÉNDICE A\nLos recursos del curso\n31 videos agrupados\n"
PAGE_APEX_B = (
    "Apéndice B. Índice de funciones de VilCretas Ejercicios y respuestas\n"
    "Función Cap. Qué hace Véase\n"
    "ArbolHuffman 6 Construye un árbol de códigos\n"
    "Productoria 1 Suma una productoria\n"
)
PAGE_APEX_C = (
    "Apéndice C. Mapa de estudio y simulacros Ejercicios y respuestas\n"
    "C.1 Capítulo 1. Recursividad\n"
    "Lo que hay que saber hacer\n"
)

PAGES = [
    PAGE_COVER,
    PAGE_TOC,
    PAGE_PART1,
    PAGE_CAP1_OPENER,
    PAGE_CAP1_BODY,
    PAGE_CAP2,
    PAGE_PART2,
    PAGE_RESP1,
    PAGE_PART3,
    PAGE_COMP1,
    PAGE_PART4,
    PAGE_TIPO1,
    PAGE_TIPO2,
    PAGE_APEX_A,
    PAGE_APEX_B,
    PAGE_APEX_C,
]


class SplitPagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = split_pages(PAGES)

    def test_chunk_files_for_every_part_and_chapter(self):
        expected = {
            "intro.md",
            "ejercicios-1.md",
            "ejercicios-2.md",
            "respuestas-1.md",
            "complementarios-1.md",
            "tipo-examen-1.md",
            "apendice-a.md",
            "apendice-b.md",
            "apendice-c.md",
            "INDICE.md",
            "funciones-vilcretas.txt",
        }
        self.assertTrue(expected.issubset(self.files), sorted(self.files))

    def test_part_title_pages_are_not_written_as_chunks(self):
        self.assertNotIn("ejercicios", self.files)
        self.assertNotIn("respuestas", self.files)
        self.assertNotIn("complementarios", self.files)
        self.assertNotIn("tipo-examen", self.files)

    def test_intro_holds_front_matter_without_leaking_categories(self):
        intro = self.files["intro.md"]

        self.assertIn("CUADERNILLO DE EJERCICIOS", intro)
        self.assertIn("Capítulo 1. Recursividad . . . 4", intro)

    def test_chunk_headers_record_page_ranges(self):
        self.assertIn("páginas 4–5 del PDF", self.files["ejercicios-1.md"])
        self.assertIn("páginas 6–6 del PDF", self.files["ejercicios-2.md"])
        self.assertIn("páginas 12–13 del PDF", self.files["tipo-examen-1.md"])
        self.assertIn("páginas 14–14 del PDF", self.files["apendice-a.md"])

    def test_chapter_via_running_header_fallback(self):
        self.assertIn("2.3.1 primera recurrencia", self.files["ejercicios-2.md"])
        self.assertIn("Capítulo 2", self.files["ejercicios-2.md"])

    def test_running_headers_and_page_numbers_are_stripped(self):
        body = self.files["ejercicios-1.md"]

        self.assertNotIn("Recursividad Ejercicios y respuestas", body)
        self.assertNotRegex(body, r"(?m)^\s*7\s*$")

    def test_toc_does_not_switch_to_appendix(self):
        self.assertIn("Apéndice A. Los recursos del curso . . . 440", self.files["intro.md"])

    def test_apendix_c_keeps_chapter_lines_inside_the_appendix(self):
        self.assertIn("C.1 Capítulo 1. Recursividad", self.files["apendice-c.md"])
        self.assertNotIn("1.7.4", self.files["apendice-c.md"])

    def test_indice_lists_files_and_exam_categories(self):
        index = self.files["INDICE.md"]

        self.assertIn("| tipo-examen-1.md | Capítulo 1 · Recursividad | 12–13 |", index)
        self.assertIn("## Categorías tipo examen por capítulo", index)
        self.assertIn("- 3-Rec. Prog. de productorias con Rec. de pila", index)
        self.assertIn("- 5-Rec. Prog. de cola", index)
        self.assertIn("capítulo.sección.ejercicio", index)

    def test_function_catalog_is_extracted_from_apendix_b(self):
        self.assertEqual(
            self.files["funciones-vilcretas.txt"],
            "ArbolHuffman\nProductoria\n",
        )

    def test_no_page_is_lost(self):
        total = "\n".join(self.files.values())

        for needle in (
            "1.5.1",
            "1.5.2",
            "2.3.1",
            "1.6.5",
            "1.7.4",
            "31 videos",
            "ArbolHuffman 6",
            "Lo que hay que saber hacer",
        ):
            self.assertIn(needle, total)


if __name__ == "__main__":
    unittest.main()
