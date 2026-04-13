from __future__ import annotations

from pathlib import Path

from calibration.optimizer import run_full_calibration


if __name__ == "__main__":
    raise SystemExit(
        run_full_calibration(
            target_csv_path=Path("virtual_mosfet_metrics_perturbed_5pct.csv")
        )
    )
