import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from optimizer import (
    CORNER_OBJECTIVE_NAMES,
    _select_starting_params,
    _score_point_errors,
    build_corner_problem,
    evaluate_corner_candidate,
    evaluate_corner_set_candidate,
    export_corner_pareto_candidates,
)
from targets import MetricTarget


class ReorderedTarget:
    def __init__(self, metric_map):
        self._metric_map = metric_map

    def as_metric_dict(self):
        return self._metric_map


class CornerNsgaTests(unittest.TestCase):
    def test_score_point_errors_penalizes_worst_case_and_mean_tail(self) -> None:
        point_errors = {
            "vtlin_v": 0.01,
            "vtsat_v": 0.02,
            "idlin_a": 0.03,
            "idsat_a": 0.04,
            "idoff_a": 0.05,
            "isoff_a": 0.06,
            "worst_relative_error": 0.06,
        }

        score = _score_point_errors(point_errors)

        self.assertAlmostEqual(score, 0.06 + 0.1 * (0.01 + 0.02 + 0.03 + 0.04 + 0.05 + 0.06) / 6.0)

    def test_evaluate_corner_candidate_returns_six_objectives_in_explicit_order(self) -> None:
        target = MetricTarget(0.14, 0.028, 1e-12, 1e-13, 0.5, 0.4, 1e-5, 1e-4)

        def simulate_fn(params):
            return {
                "vtlin_v": 0.52,
                "vtsat_v": 0.38,
                "idlin_a": 1.1e-5,
                "idsat_a": 0.9e-4,
                "idoff_a": 1.2e-12,
                "isoff_a": 1.1e-13,
            }

        result = evaluate_corner_candidate(target, {"vth0": 0.3}, simulate_fn)

        self.assertEqual(len(result), 6)
        self.assertEqual(CORNER_OBJECTIVE_NAMES, ("vtlin_v", "vtsat_v", "idlin_a", "idsat_a", "idoff_a", "isoff_a"))
        for actual, expected in zip(result, [0.04, 0.05, 0.1, 0.1, 0.2, 0.1], strict=True):
            self.assertAlmostEqual(actual, expected)

    def test_build_corner_problem_evaluates_corner_vector_and_exports_pareto_rows(self) -> None:
        target = MetricTarget(0.14, 0.028, 1e-12, 1e-13, 0.5, 0.4, 1e-5, 1e-4)
        corner_targets = {
            "w_min_l_min": target,
            "w_min_l_max": target,
            "w_max_l_min": target,
            "w_max_l_max": target,
        }

        def simulate_fn(params):
            return {
                "vtlin_v": 0.5 + params["vth0"],
                "vtsat_v": 0.4 + params["vth0"],
                "idlin_a": 1e-5 * (1.0 + params["vth0"]),
                "idsat_a": 1e-4 * (1.0 + params["vth0"]),
                "idoff_a": 1e-12 * (1.0 + params["vth0"]),
                "isoff_a": 1e-13 * (1.0 + params["vth0"]),
            }

        problem = build_corner_problem(corner_targets, simulate_fn)
        vector = [0.0] * problem.n_var
        objectives = problem.evaluate([vector], return_values_of=["F"]).tolist()

        self.assertEqual(objectives, [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pareto_candidates.csv"
            export_corner_pareto_candidates(path, [vector], objectives)

            contents = path.read_text(encoding="utf-8")

        self.assertIn("candidate_id", contents)
        self.assertIn("vtlin_v", contents)
        self.assertIn("w_min_l_min__toxe", contents)

    def test_build_corner_problem_rejects_missing_or_extra_corners(self) -> None:
        target = MetricTarget(0.14, 0.028, 1e-12, 1e-13, 0.5, 0.4, 1e-5, 1e-4)

        with self.assertRaisesRegex(ValueError, "missing"):
            build_corner_problem(
                {
                    "w_min_l_min": target,
                    "w_min_l_max": target,
                    "w_max_l_min": target,
                },
                lambda params: {},
            )

        with self.assertRaisesRegex(ValueError, "unexpected"):
            build_corner_problem(
                {
                    "w_min_l_min": target,
                    "w_min_l_max": target,
                    "w_max_l_min": target,
                    "w_max_l_max": target,
                    "extra_corner": target,
                },
                lambda params: {},
            )

    def test_evaluate_corner_set_candidate_maps_objectives_by_explicit_metric_names(self) -> None:
        reordered_target = ReorderedTarget(
            {
                "isoff_a": 1e-13,
                "idoff_a": 1e-12,
                "idsat_a": 1e-4,
                "idlin_a": 1e-5,
                "vtsat_v": 0.4,
                "vtlin_v": 0.5,
            }
        )
        corner_targets = {
            "w_min_l_min": reordered_target,
            "w_min_l_max": reordered_target,
            "w_max_l_min": reordered_target,
            "w_max_l_max": reordered_target,
        }

        result = evaluate_corner_set_candidate(
            corner_targets,
            {
                "w_min_l_min": {"vth0": 0.0},
                "w_min_l_max": {"vth0": 0.0},
                "w_max_l_min": {"vth0": 0.0},
                "w_max_l_max": {"vth0": 0.0},
            },
            lambda params: {
                "vtlin_v": 0.55,
                "vtsat_v": 0.42,
                "idlin_a": 1.2e-5,
                "idsat_a": 0.8e-4,
                "idoff_a": 1.5e-12,
                "isoff_a": 0.9e-13,
            },
        )

        self.assertEqual(list(result.keys()), list(CORNER_OBJECTIVE_NAMES))
        for actual, expected in zip(result.values(), [0.1, 0.05, 0.2, 0.2, 0.5, 0.1], strict=True):
            self.assertAlmostEqual(actual, expected)

    def test_select_starting_params_picks_lowest_scoring_candidate(self) -> None:
        target = MetricTarget(0.14, 0.028, 1e-12, 1e-13, 0.5, 0.4, 1e-5, 1e-4)
        baseline = {"vth0": 0.3}
        surface = {"vth0": 0.2}
        blended = {"vth0": 0.25}
        score_map = {
            id(baseline): {
                "vtlin_v": 0.05,
                "vtsat_v": 0.04,
                "idlin_a": 0.05,
                "idsat_a": 0.04,
                "idoff_a": 0.02,
                "isoff_a": 0.02,
                "worst_relative_error": 0.05,
            },
            id(surface): {
                "vtlin_v": 0.03,
                "vtsat_v": 0.02,
                "idlin_a": 0.03,
                "idsat_a": 0.02,
                "idoff_a": 0.01,
                "isoff_a": 0.01,
                "worst_relative_error": 0.03,
            },
            id(blended): {
                "vtlin_v": 0.04,
                "vtsat_v": 0.03,
                "idlin_a": 0.04,
                "idsat_a": 0.03,
                "idoff_a": 0.02,
                "isoff_a": 0.02,
                "worst_relative_error": 0.04,
            },
        }

        with (
            patch("src.optimizer._candidate_starting_params", return_value=[baseline, surface, blended]),
            patch(
                "src.optimizer._point_summary",
                side_effect=lambda _target, params: ({}, score_map[id(params)]),
            ),
        ):
            selected, score = _select_starting_params(target, surface_models={})

        self.assertIs(selected, surface)
        self.assertAlmostEqual(score, _score_point_errors(score_map[id(surface)]))

    def test_export_corner_pareto_candidates_writes_header_for_empty_candidate_sets(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pareto_candidates.csv"

            export_corner_pareto_candidates(path, [], [])

            contents = path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(contents), 1)
        self.assertIn("candidate_id", contents[0])
        self.assertIn("vtlin_v", contents[0])
        self.assertIn("w_max_l_max__keta", contents[0])
