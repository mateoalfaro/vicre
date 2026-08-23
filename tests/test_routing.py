import subprocess
import unittest
from unittest import mock

from vicre.routing import infer_expected_procedures, ocr_image


class RoutingTests(unittest.TestCase):
    def test_recurrence_experiment_fingerprint_routes_repeated_timing(self):
        text = """
        Considere cuatro algoritmos f1 f2 f3 f4 que calculan una recurrencia.
        El experimento toma n entre 5 y 20 con incremento 1.
        """

        self.assertEqual(infer_expected_procedures(text), ("timing_repeated",))

    def test_recurrence_fingerprint_tolerates_observed_ocr_errors(self):
        text = '''
        Considere s sguientes 4 aigorimos que realzan a misma tarea.
        filndi=f1l-11-filn-21 + il-3] f2ln-1]-2In-2]+f2[n-3]
        labors i exerimerto paran e 20. Ordene los metodos por rapidez.
        '''

        self.assertEqual(infer_expected_procedures(text), ("timing_repeated",))

    def test_recurrence_fingerprint_tolerates_spanish_ocr_joined_range(self):
        text = '''
        Considere los siguientes 4 algoritmos. filndi f2ln-1.
        Elabore un exermento para n en 5y20 y ordene los métodos.
        '''

        self.assertEqual(infer_expected_procedures(text), ("timing_repeated",))

    def test_even_digit_fingerprint_routes_numeric_and_graphica(self):
        text = """
        Para n=859745621 compare f y g. Use valores de 1 a 200 con incremento 20.
        Prueba ADA Grafica en el examen.
        """

        self.assertEqual(
            set(infer_expected_procedures(text)),
            {"numeric_compare", "timing_graphica"},
        )

    def test_even_digit_fingerprint_tolerates_one_wrong_leading_digit(self):
        text = '''
        Considre dos metodos. El valor cuando n = 8507456215.
        El metodo que usa recursividad de cola. Valores de 1 a 12200,
        cremento do20.
        '''

        self.assertEqual(
            set(infer_expected_procedures(text)),
            {"numeric_compare", "timing_graphica"},
        )

    def test_two_method_recursion_fingerprint_survives_missing_number(self):
        text = '''
        Considere los siguientes dos metodos. El metodo que usa recursividad.
        Enfoque experimental usando valores de 1 a 200 con un incremento
        de 20.
        '''

        self.assertEqual(
            set(infer_expected_procedures(text)),
            {"numeric_compare", "timing_graphica"},
        )

    def test_spanish_suma_is_not_mistaken_for_wolfram_sum(self):
        text = "Module con variable suma para dos metodos"

        self.assertEqual(infer_expected_procedures(text), ())

    def test_four_algorithms_without_experiment_is_not_forced_to_timing(self):
        text = "Cuatro algoritmos f1 f2 calculan f[20]"

        self.assertEqual(infer_expected_procedures(text), ())

    def test_sum_for_cycle_iterations_routes_loop_count(self):
        text = "Use Sum para contar las iteraciones de los ciclos"

        self.assertEqual(infer_expected_procedures(text), ("loop_count",))

    def test_command_names_are_case_and_ocr_space_tolerant(self):
        text = "Repeated Timing + List Line Plot; Comp Limit; Find Sequence Function"

        self.assertEqual(
            set(infer_expected_procedures(text)),
            {"timing_repeated", "comp_limit", "loop_count"},
        )

    def test_tesseract_failure_fails_open(self):
        with mock.patch(
            "vicre.routing.subprocess.run",
            side_effect=OSError("not installed"),
        ):
            self.assertEqual(ocr_image("/tmp/capture.png"), "")

    def test_tesseract_timeout_fails_open_and_uses_psm_6(self):
        with mock.patch(
            "vicre.routing.subprocess.run",
            side_effect=subprocess.TimeoutExpired("tesseract", 5),
        ) as run:
            self.assertEqual(ocr_image("/tmp/capture.png"), "")

        args, kwargs = run.call_args
        self.assertIn("--psm", args[0])
        self.assertIn("6", args[0])
        self.assertIn("spa+eng", args[0])
        self.assertLessEqual(kwargs["timeout"], 5)


if __name__ == "__main__":
    unittest.main()
