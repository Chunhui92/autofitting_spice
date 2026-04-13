import unittest

from calibration.global_refit import fit_global_parameter_plane


class GlobalRefitTests(unittest.TestCase):
    def test_fit_global_parameter_plane_rejects_empty_samples(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one sample"):
            fit_global_parameter_plane("vth0", [])

    def test_fit_global_parameter_plane_returns_callable_model(self) -> None:
        samples = [
            {"w_um": 0.14, "l_um": 0.028, "vth0": 0.25},
            {"w_um": 5.4, "l_um": 2.7, "vth0": 0.45},
        ]

        model = fit_global_parameter_plane("vth0", samples)

        self.assertTrue(callable(model))

    def test_fit_global_parameter_plane_interpolates_smoothly_in_log_space(self) -> None:
        samples = [
            {"w_um": 0.14, "l_um": 0.028, "vth0": 0.25},
            {"w_um": 5.4, "l_um": 2.7, "vth0": 0.45},
        ]

        model = fit_global_parameter_plane("vth0", samples)

        self.assertAlmostEqual(model(0.14, 0.028), 0.25)
        self.assertAlmostEqual(model(5.4, 2.7), 0.45)
        self.assertAlmostEqual(model((0.14 * 5.4) ** 0.5, (0.028 * 2.7) ** 0.5), 0.35, places=2)
