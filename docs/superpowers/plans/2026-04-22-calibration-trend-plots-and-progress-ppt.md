# Calibration Trend Plots And Progress PPT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two calibration parameter trend figures, regenerate calibration artifacts, and produce a reusable 8-10 page project progress PPT that embeds the latest result images.

**Architecture:** Extend the existing matplotlib reporting pipeline so calibration output generation emits two additional parameter trend summary figures based on the calibrated parameter table. Add a standalone PPT builder script that reads the latest calibration summary, CSV diagnostics, and generated PNG artifacts to produce a presentation without changing the optimization core.

**Tech Stack:** Python, matplotlib, csv, pathlib, python-pptx in the `spice` environment

---

### Task 1: Add plot coverage for parameter trend summary figures

**Files:**
- Modify: `tests/test_plotting.py`
- Modify: `src/plotting.py`
- Modify: `src/reporting.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_plot_parameter_trends_vs_width_writes_png(self) -> None:
    ...

def test_plot_parameter_trends_vs_length_writes_png(self) -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_plotting.PlottingTests.test_plot_parameter_trends_vs_width_writes_png -v`
Expected: FAIL with `ImportError` or `AttributeError` for the missing plotting helper

- [ ] **Step 3: Write minimal implementation**

```python
def plot_parameter_trend_grid(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_plotting -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_plotting.py src/plotting.py src/reporting.py
git commit -m "Add calibration parameter trend plots"
```

### Task 2: Wire new figures into calibration output generation

**Files:**
- Modify: `src/optimizer.py`
- Modify: `tests/test_plotting.py`

- [ ] **Step 1: Write the failing integration assertion**

```python
self.assertTrue((output_dir / "parameter_trends_vs_w.png").exists())
self.assertTrue((output_dir / "parameter_trends_vs_l.png").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_plotting.PlottingTests.test_write_calibration_plots_emits_core_output_files -v`
Expected: FAIL because the new output files are not created yet

- [ ] **Step 3: Write minimal implementation**

```python
_generate_plots(...)
write_calibration_plots(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_plotting -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/optimizer.py tests/test_plotting.py
git commit -m "Emit calibration trend plot artifacts"
```

### Task 3: Add reusable progress presentation generator

**Files:**
- Create: `scripts/build_progress_ppt.py`
- Modify: `README.md`

- [ ] **Step 1: Build the script around existing artifact paths**

```python
def main() -> int:
    ...
```

- [ ] **Step 2: Run the generator in the `spice` environment**

Run: `MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/build_progress_ppt.py`
Expected: writes a `.pptx` file into `artifacts/calibration_output/`

- [ ] **Step 3: Document the command**

```markdown
- `conda run -n spice python scripts/build_progress_ppt.py`
```

- [ ] **Step 4: Commit**

```bash
git add scripts/build_progress_ppt.py README.md
git commit -m "Add project progress presentation builder"
```

### Task 4: Regenerate outputs and verify end to end

**Files:**
- Update generated artifacts under: `artifacts/calibration_output/`

- [ ] **Step 1: Regenerate calibration outputs**

Run: `MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/run_calibration.py`
Expected: completes and refreshes CSV, Markdown, and PNG outputs

- [ ] **Step 2: Generate the presentation**

Run: `MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/build_progress_ppt.py`
Expected: writes the final `.pptx`

- [ ] **Step 3: Run verification**

Run: `MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest discover -s tests -v`
Expected: PASS

- [ ] **Step 4: Commit and publish**

```bash
git add .
git commit -m "Add calibration trend plots and project progress deck"
git push
```
