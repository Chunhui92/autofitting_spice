from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
SCRIPTS_DIR = ROOT_DIR / "scripts"
DATA_DIR = ROOT_DIR / "data"
TARGETS_DIR = DATA_DIR / "targets"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
CALIBRATION_OUTPUT_DIR = ARTIFACTS_DIR / "calibration_output"
DATASET_OUTPUT_DIR = ARTIFACTS_DIR / "dataset_generation"
DEFAULT_TARGET_CSV = TARGETS_DIR / "virtual_mosfet_metrics_perturbed_5pct.csv"
