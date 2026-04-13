import unittest

from parameter_bounds import PARAMETER_NAMES, default_parameter_guess, parameter_bounds


class ParameterBoundsTests(unittest.TestCase):
    def test_parameter_names_match_expected_order(self) -> None:
        self.assertEqual(
            PARAMETER_NAMES,
            [
                "toxe", "vth0", "u0", "vsat", "rdsw", "nfactor", "eta0",
                "cit", "voff", "k2", "ub", "uc", "a0", "keta",
            ],
        )

    def test_default_guess_is_within_bounds(self) -> None:
        guess = default_parameter_guess()
        bounds = parameter_bounds()
        for name in PARAMETER_NAMES:
            lower, upper = bounds[name]
            self.assertGreaterEqual(guess[name], lower)
            self.assertLessEqual(guess[name], upper)
