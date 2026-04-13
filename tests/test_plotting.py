import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from plotting import (
    build_metric_grid,
    plot_error_heatmap,
    plot_pareto_front,
    plot_target_vs_simulated,
)
from reporting import write_calibration_plots


class PlottingTests(unittest.TestCase):
    def test_build_metric_grid_returns_matrix_shape(self) -> None:
        rows = [
            {"w_um": 0.14, "l_um": 0.028, "relative_error": 0.1},
            {"w_um": 0.14, "l_um": 0.056, "relative_error": 0.2},
        ]

        widths, lengths, grid = build_metric_grid(rows, value_key="relative_error")

        self.assertEqual(len(widths), 1)
        self.assertEqual(len(lengths), 2)
        self.assertEqual(grid.shape, (1, 2))
        self.assertAlmostEqual(grid[0, 0], 0.1)
        self.assertAlmostEqual(grid[0, 1], 0.2)

    def test_plot_error_heatmap_writes_png(self) -> None:
        rows = [
            {"w_um": 0.14, "l_um": 0.028, "relative_error": 0.1},
            {"w_um": 0.14, "l_um": 0.056, "relative_error": 0.2},
            {"w_um": 0.28, "l_um": 0.028, "relative_error": 0.3},
            {"w_um": 0.28, "l_um": 0.056, "relative_error": 0.4},
        ]

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "error_heatmap.png"
            plot_error_heatmap(path, rows, metric_name="vtlin_v", value_key="relative_error")

            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

    def test_plot_pareto_front_writes_png(self) -> None:
        rows = [
            {"candidate_id": 1, "vtlin_v": 0.10, "idsat_a": 0.08},
            {"candidate_id": 2, "vtlin_v": 0.08, "idsat_a": 0.11},
        ]

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pareto_front.png"
            plot_pareto_front(path, rows, x_metric="vtlin_v", y_metric="idsat_a")

            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

    def test_plot_target_vs_simulated_writes_png(self) -> None:
        rows = [
            {"metric_name": "vtlin_v", "target_value": 0.45, "simulated_value": 0.47},
            {"metric_name": "vtlin_v", "target_value": 0.55, "simulated_value": 0.53},
        ]

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "target_vs_simulated.png"
            plot_target_vs_simulated(path, rows, metric_name="vtlin_v")

            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)

    def test_write_calibration_plots_emits_core_output_files(self) -> None:
        pareto_rows = [
            {"candidate_id": 1, "vtlin_v": 0.10, "idsat_a": 0.08},
            {"candidate_id": 2, "vtlin_v": 0.08, "idsat_a": 0.11},
        ]
        error_rows = [
            {"w_um": 0.14, "l_um": 0.028, "metric_name": "vtlin_v", "target_value": 0.45, "simulated_value": 0.47, "relative_error": 0.04},
            {"w_um": 0.14, "l_um": 0.056, "metric_name": "vtlin_v", "target_value": 0.55, "simulated_value": 0.53, "relative_error": 0.03},
            {"w_um": 0.28, "l_um": 0.028, "metric_name": "vtlin_v", "target_value": 0.49, "simulated_value": 0.50, "relative_error": 0.02},
            {"w_um": 0.28, "l_um": 0.056, "metric_name": "vtlin_v", "target_value": 0.59, "simulated_value": 0.57, "relative_error": 0.03},
        ]
        parameter_rows = [
            {"w_um": 0.14, "l_um": 0.028, "vth0": 0.21},
            {"w_um": 0.14, "l_um": 0.056, "vth0": 0.24},
            {"w_um": 0.28, "l_um": 0.028, "vth0": 0.31},
            {"w_um": 0.28, "l_um": 0.056, "vth0": 0.34},
        ]

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            write_calibration_plots(
                output_dir=output_dir,
                pareto_rows=pareto_rows,
                error_rows=error_rows,
                parameter_rows=parameter_rows,
                parameter_names=["vth0"],
            )

            self.assertTrue((output_dir / "pareto_front_vtlin_v_vs_idsat_a.png").exists())
            self.assertTrue((output_dir / "error_heatmap_vtlin_v.png").exists())
            self.assertTrue((output_dir / "target_vs_simulated_vtlin_v.png").exists())
            self.assertTrue((output_dir / "parameter_surface_vth0.png").exists())
