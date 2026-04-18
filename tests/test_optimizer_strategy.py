import unittest

from src.optimizer import CalibrationStrategy, _focus_metric_names, _score_point_errors


class OptimizerStrategyTests(unittest.TestCase):
    def test_default_strategy_raises_search_budget_above_bootstrap_values(self) -> None:
        strategy = CalibrationStrategy()

        self.assertGreater(strategy.corner_pop_size, 12)
        self.assertGreater(strategy.corner_generations, 4)
        self.assertGreater(strategy.local_maxiter, 20)
        self.assertGreater(strategy.local_maxfev, 150)
        self.assertGreater(strategy.de_maxiter, 12)
        self.assertGreater(strategy.de_popsize, 6)

    def test_score_point_errors_prioritizes_leakage_metrics(self) -> None:
        leakage_heavy = {
            "vtlin_v": 0.020,
            "vtsat_v": 0.020,
            "idlin_a": 0.020,
            "idsat_a": 0.020,
            "idoff_a": 0.040,
            "isoff_a": 0.039,
            "worst_relative_error": 0.040,
        }
        non_leakage_heavy = {
            "vtlin_v": 0.040,
            "vtsat_v": 0.039,
            "idlin_a": 0.020,
            "idsat_a": 0.020,
            "idoff_a": 0.020,
            "isoff_a": 0.020,
            "worst_relative_error": 0.040,
        }

        strategy = CalibrationStrategy(leakage_metric_weight=1.5)

        leakage_score = _score_point_errors(leakage_heavy, strategy)
        non_leakage_score = _score_point_errors(non_leakage_heavy, strategy)

        self.assertGreater(leakage_score, non_leakage_score)

    def test_focus_metric_names_keeps_nearby_leakage_metrics(self) -> None:
        point_errors = {
            "vtlin_v": 0.050,
            "vtsat_v": 0.018,
            "idlin_a": 0.010,
            "idsat_a": 0.015,
            "idoff_a": 0.031,
            "isoff_a": 0.030,
            "worst_relative_error": 0.050,
        }

        strategy = CalibrationStrategy(leakage_metric_weight=1.5, leakage_focus_threshold_ratio=0.6)
        focus_metrics = _focus_metric_names(point_errors, strategy)

        self.assertIn("vtlin_v", focus_metrics)
        self.assertIn("idoff_a", focus_metrics)
        self.assertIn("isoff_a", focus_metrics)
