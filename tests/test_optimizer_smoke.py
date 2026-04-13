import unittest

from parameter_bounds import default_parameter_guess
from simulator import simulate_metrics_for_point


class SimulatorSmokeTests(unittest.TestCase):
    def test_simulate_metrics_for_point_returns_expected_keys(self) -> None:
        metrics = simulate_metrics_for_point(
            w_um=0.14,
            l_um=0.028,
            model_params=default_parameter_guess(),
        )
        self.assertEqual(
            sorted(metrics.keys()),
            ["idlin_a", "idoff_a", "idsat_a", "isoff_a", "vtlin_v", "vtsat_v"],
        )
