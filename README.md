# autofitting_spice

PySpice-based BSIM4 dataset generation and multi-stage calibration workflow for 42 `W/L` device targets.

## Project Structure

```text
.
├── src/calibration/            # Core package: simulation, optimization, plotting, targets, paths
├── scripts/                    # Preferred executable entry points
├── data/targets/               # Input target CSV files
├── artifacts/                  # Runtime-generated outputs, ignored by git
├── tests/                      # Unit and smoke tests
├── docs/                       # Specs and implementation plans
├── bsim4_dataset.py            # Backward-compatible wrapper for dataset generation
└── run_calibration.py          # Backward-compatible wrapper for calibration
```

## Recommended Commands

Run dataset generation:

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/generate_bsim4_dataset.py
```

Run calibration:

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run --no-capture-output -n spice python scripts/run_calibration.py
```

Run all tests:

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest discover -s tests -v
```

## Key Paths

- Default target CSV: `data/targets/virtual_mosfet_metrics_perturbed_5pct.csv`
- Calibration outputs: `artifacts/calibration_output/`
- Dataset outputs: `artifacts/dataset_generation/`

## Notes

- Core path defaults are centralized in `src/calibration/project_paths.py`.
- CLI entry points are centralized in `src/calibration/cli.py`.
- The current calibration pipeline is stable and tested, but the current best worst-case relative error is still about `5.1%`, so the `<3%` target has not yet been reached.
