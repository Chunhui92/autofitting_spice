from pathlib import Path
import unittest
import tempfile

from project_paths import DEFAULT_TARGET_CSV
from targets import MetricTargetSet


def _workspace_csv_path() -> Path:
    return DEFAULT_TARGET_CSV


class MetricTargetSetTests(unittest.TestCase):
    def test_load_targets_builds_lookup_by_size(self) -> None:
        targets = MetricTargetSet.from_csv(_workspace_csv_path())
        target = targets.get(0.14, 0.028)
        self.assertEqual((target.w_um, target.l_um), (0.14, 0.028))
        self.assertEqual(
            sorted(target.as_metric_dict().keys()),
            ["idlin_a", "idoff_a", "idsat_a", "isoff_a", "vtlin_v", "vtsat_v"],
        )

    def test_missing_size_raises_key_error(self) -> None:
        targets = MetricTargetSet.from_csv(_workspace_csv_path())
        with self.assertRaises(KeyError):
            targets.get(9.9, 9.9)

    def test_duplicate_size_rows_raise_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "duplicate_targets.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "w_um,l_um,idoff_a,isoff_a,vtlin_v,vtsat_v,idlin_a,idsat_a",
                        "0.14,0.028,1,2,3,4,5,6",
                        "0.14,0.028,7,8,9,10,11,12",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                MetricTargetSet.from_csv(csv_path)
