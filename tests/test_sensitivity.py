import unittest

from sensitivity import finite_difference_sensitivity


class SensitivityTests(unittest.TestCase):
    def test_finite_difference_sensitivity_returns_metric_map(self) -> None:
        def evaluator(params: dict[str, float]) -> dict[str, float]:
            return {"vtlin_v": params["vth0"] * 2.0, "idsat_a": params["u0"] * 1e-6}

        result = finite_difference_sensitivity(
            base_params={"vth0": 0.3, "u0": 400.0},
            parameter_steps={"vth0": 0.01, "u0": 1.0},
            evaluator=evaluator,
        )
        self.assertIn("vth0", result)
        self.assertIn("vtlin_v", result["vth0"])
        self.assertGreater(result["vth0"]["vtlin_v"], 0.0)

    def test_finite_difference_sensitivity_falls_back_when_forward_step_fails(self) -> None:
        def evaluator(params: dict[str, float]) -> dict[str, float]:
            if params["vth0"] > 0.3:
                raise RuntimeError("forward step invalid")
            return {"vtlin_v": params["vth0"] * 2.0}

        result = finite_difference_sensitivity(
            base_params={"vth0": 0.3},
            parameter_steps={"vth0": 0.01},
            evaluator=evaluator,
        )
        self.assertAlmostEqual(result["vth0"]["vtlin_v"], 2.0)
