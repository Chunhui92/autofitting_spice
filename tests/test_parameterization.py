import unittest

from src.parameterization import BilinearSurfaceModel, CornerParameterSet


class ParameterizationTests(unittest.TestCase):
    def test_bilinear_surface_hits_corner_values_exactly(self) -> None:
        corners = CornerParameterSet(
            w_min_l_min={"vth0": 0.2},
            w_min_l_max={"vth0": 0.3},
            w_max_l_min={"vth0": 0.4},
            w_max_l_max={"vth0": 0.5},
        )
        surface = BilinearSurfaceModel.from_corners(
            parameter_name="vth0",
            corners=corners,
            w_bounds=(0.14, 5.4),
            l_bounds=(0.028, 2.7),
        )
        self.assertAlmostEqual(surface.evaluate(0.14, 0.028), 0.2)
        self.assertAlmostEqual(surface.evaluate(0.14, 2.7), 0.3)
        self.assertAlmostEqual(surface.evaluate(5.4, 0.028), 0.4)
        self.assertAlmostEqual(surface.evaluate(5.4, 2.7), 0.5)

    def test_surface_value_is_continuous_inside_domain(self) -> None:
        corners = CornerParameterSet(
            w_min_l_min={"u0": 200.0},
            w_min_l_max={"u0": 300.0},
            w_max_l_min={"u0": 500.0},
            w_max_l_max={"u0": 600.0},
        )
        surface = BilinearSurfaceModel.from_corners("u0", corners, (0.14, 5.4), (0.028, 2.7))
        left = surface.evaluate(0.56, 0.14)
        right = surface.evaluate(0.5601, 0.1401)
        self.assertLess(abs(right - left), 1.0)

    def test_surface_clamps_out_of_range_inputs_to_domain_edges(self) -> None:
        corners = CornerParameterSet(
            w_min_l_min={"vth0": 0.2},
            w_min_l_max={"vth0": 0.3},
            w_max_l_min={"vth0": 0.4},
            w_max_l_max={"vth0": 0.5},
        )
        surface = BilinearSurfaceModel.from_corners("vth0", corners, (0.14, 5.4), (0.028, 2.7))

        self.assertAlmostEqual(surface.evaluate(0.01, 0.028), 0.2)
        self.assertAlmostEqual(surface.evaluate(5.4, 10.0), 0.5)
        self.assertAlmostEqual(surface.evaluate(10.0, 0.001), 0.4)
