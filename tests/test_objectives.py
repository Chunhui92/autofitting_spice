import unittest

from objectives import aggregate_metric_objectives


class ObjectiveAggregationTests(unittest.TestCase):
    def test_aggregate_metric_objectives_returns_six_worst_case_values(self) -> None:
        rows = [
            {
                "vtlin_v": 0.01,
                "vtsat_v": 0.02,
                "idlin_a": 0.03,
                "idsat_a": 0.04,
                "idoff_a": 0.05,
                "isoff_a": 0.06,
            },
            {
                "vtlin_v": 0.015,
                "vtsat_v": 0.01,
                "idlin_a": 0.01,
                "idsat_a": 0.05,
                "idoff_a": 0.02,
                "isoff_a": 0.03,
            },
        ]

        result = aggregate_metric_objectives(rows)

        self.assertEqual(
            sorted(result.keys()),
            ["idlin_a", "idoff_a", "idsat_a", "isoff_a", "vtlin_v", "vtsat_v"],
        )
        self.assertAlmostEqual(result["vtlin_v"], 0.015)
        self.assertAlmostEqual(result["idsat_a"], 0.05)
