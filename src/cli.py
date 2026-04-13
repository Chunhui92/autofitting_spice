from __future__ import annotations

import argparse

from .project_paths import CALIBRATION_OUTPUT_DIR, DATASET_OUTPUT_DIR, DEFAULT_TARGET_CSV


def main_run_calibration() -> int:
    parser = argparse.ArgumentParser(description="Run the PySpice multi-stage calibration workflow.")
    parser.add_argument(
        "--target-csv",
        default=str(DEFAULT_TARGET_CSV),
        help="Path to the target metrics CSV.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(CALIBRATION_OUTPUT_DIR),
        help="Directory for calibration artifacts.",
    )
    args = parser.parse_args()
    from .optimizer import run_full_calibration

    return run_full_calibration(target_csv_path=args.target_csv, output_dir=args.output_dir)


def main_generate_dataset() -> int:
    parser = argparse.ArgumentParser(description="Generate the virtual BSIM4 dataset and summary plots.")
    parser.add_argument(
        "--output-dir",
        default=str(DATASET_OUTPUT_DIR),
        help="Directory for generated dataset artifacts.",
    )
    args = parser.parse_args()
    from .dataset_generator import main as generate_dataset

    generate_dataset(output_dir=args.output_dir)
    return 0
