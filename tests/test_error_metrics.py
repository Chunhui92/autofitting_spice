import unittest

from src.error_metrics import relative_error, summarize_point_errors


class ErrorMetricTests(unittest.TestCase):
    def test_relative_error_uses_absolute_target_denominator(self) -> None:
        self.assertAlmostEqual(relative_error(103.0, 100.0), 0.03)
        self.assertAlmostEqual(relative_error(97.0, 100.0), 0.03)

    def test_relative_error_handles_zero_target(self) -> None:
        self.assertEqual(relative_error(0.0, 0.0), 0.0)
        self.assertEqual(relative_error(1.0, 0.0), float("inf"))

    def test_summarize_point_errors_returns_worst_metric(self) -> None:
        errors = summarize_point_errors(
            simulated={"vtlin_v": 0.515, "idsat_a": 1.07e-4},
            target={"vtlin_v": 0.5, "idsat_a": 1.0e-4},
        )
        self.assertEqual(errors["worst_metric"], "idsat_a")
        self.assertGreater(errors["worst_relative_error"], 0.06)
