import unittest

from local_tuning import bounded_local_box


class LocalTuningTests(unittest.TestCase):
    def test_bounded_local_box_stays_inside_global_bounds(self) -> None:
        box = bounded_local_box(
            base_params={"vth0": 0.3},
            global_bounds={"vth0": (0.1, 0.5)},
            relative_radius=0.1,
        )

        self.assertEqual(box["vth0"], (0.27, 0.33))

    def test_bounded_local_box_clips_to_global_bounds(self) -> None:
        box = bounded_local_box(
            base_params={"vth0": 0.12, "u0": 880.0},
            global_bounds={"vth0": (0.1, 0.5), "u0": (150.0, 900.0)},
            relative_radius=0.2,
        )

        self.assertEqual(box["vth0"], (0.1, 0.144))
        self.assertEqual(box["u0"], (704.0, 900.0))

    def test_bounded_local_box_handles_negative_base_values(self) -> None:
        box = bounded_local_box(
            base_params={"voff": -0.2},
            global_bounds={"voff": (-0.35, 0.05)},
            relative_radius=0.1,
        )

        self.assertAlmostEqual(box["voff"][0], -0.22)
        self.assertAlmostEqual(box["voff"][1], -0.18)
