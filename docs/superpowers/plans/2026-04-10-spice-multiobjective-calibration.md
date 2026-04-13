# Spice Multiobjective Calibration Implementation Plan

> Note: 这是历史实施计划文档，已按当前仓库结构同步路径与入口；其中部分任务描述保留了当时的执行语境，主要用于追溯实施过程。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一套基于 `pymoo/NSGA-II` 的多目标 SPICE 参数校准流程，支持 4 角点优化、连续曲面初始化、逐器件局部微调、全局再拟合、最终精修，并输出 CSV 与绘图结果。

**Architecture:** 在现有 `src` 包基础上，新增多目标问题定义、角点 Pareto 搜索、逐器件局部微调、全局再拟合和绘图模块。数据流按“目标 CSV -> 仿真评估 -> 多目标优化 -> 中间教师解 -> 全局连续模型 -> 报告与图形”推进，最终由 `run_calibration.py` 统一驱动。

**Tech Stack:** Python, PySpice, numpy, matplotlib, pymoo, unittest

---

当前工作区不是 git 仓库，本计划不包含 `git commit` 步骤。计划默认目标文件为 `data/targets/virtual_mosfet_metrics_perturbed_5pct.csv`。

## File Structure

- Modify: `src/targets.py`
- Modify: `src/error_metrics.py`
- Modify: `src/parameterization.py`
- Modify: `src/optimizer.py`
- Modify: `src/reporting.py`
- Modify: `src/simulator.py`
- Modify: `run_calibration.py`
- Modify: `pyspice_run.md`
- Create: `src/objectives.py`
- Create: `src/pymoo_problem.py`
- Create: `src/local_tuning.py`
- Create: `src/global_refit.py`
- Create: `src/plotting.py`
- Create: `tests/test_objectives.py`
- Create: `tests/test_pymoo_problem.py`
- Create: `tests/test_local_tuning.py`
- Create: `tests/test_global_refit.py`
- Create: `tests/test_plotting.py`

### Task 1: 切换目标数据入口并补齐目标/误差聚合接口

**Files:**
- Modify: `src/targets.py`
- Modify: `src/error_metrics.py`
- Create: `src/objectives.py`
- Create: `tests/test_objectives.py`

- [ ] **Step 1: 写 6 目标聚合的失败测试**

```python
# tests/test_objectives.py
import unittest

from src.objectives import aggregate_metric_objectives


class ObjectiveAggregationTests(unittest.TestCase):
    def test_aggregate_metric_objectives_returns_six_worst_case_values(self) -> None:
        rows = [
            {"vtlin_v": 0.01, "vtsat_v": 0.02, "idlin_a": 0.03, "idsat_a": 0.04, "idoff_a": 0.05, "isoff_a": 0.06},
            {"vtlin_v": 0.015, "vtsat_v": 0.01, "idlin_a": 0.01, "idsat_a": 0.05, "idoff_a": 0.02, "isoff_a": 0.03},
        ]
        result = aggregate_metric_objectives(rows)
        self.assertEqual(sorted(result.keys()), ["idoff_a", "idlin_a", "idsat_a", "isoff_a", "vtlin_v", "vtsat_v"])
        self.assertAlmostEqual(result["vtlin_v"], 0.015)
        self.assertAlmostEqual(result["idsat_a"], 0.05)
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_objectives -v
```

Expected: import failure for `src.objectives`

- [ ] **Step 3: 实现目标聚合与目标文件默认路径切换**

```python
# src/objectives.py
from __future__ import annotations

METRIC_NAMES = ["vtlin_v", "vtsat_v", "idlin_a", "idsat_a", "idoff_a", "isoff_a"]


def aggregate_metric_objectives(point_error_rows: list[dict[str, float]]) -> dict[str, float]:
    return {
        metric_name: max(row[metric_name] for row in point_error_rows)
        for metric_name in METRIC_NAMES
    }
```

```python
# run_calibration.py
from pathlib import Path

from src.optimizer import run_full_calibration


if __name__ == "__main__":
    raise SystemExit(
        run_full_calibration(
            target_csv_path=Path("data/targets/virtual_mosfet_metrics_perturbed_5pct.csv"),
        )
    )
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_objectives -v
```

Expected: all tests `OK`

### Task 2: 定义 4 角点多目标问题与 `pymoo` 接口

**Files:**
- Create: `src/pymoo_problem.py`
- Create: `tests/test_pymoo_problem.py`
- Modify: `src/optimizer.py`

- [ ] **Step 1: 写角点问题编码/解码失败测试**

```python
# tests/test_pymoo_problem.py
import unittest

from src.parameter_bounds import PARAMETER_NAMES
from src.pymoo_problem import CornerProblemLayout


class PymooProblemTests(unittest.TestCase):
    def test_corner_problem_layout_has_expected_variable_count(self) -> None:
        layout = CornerProblemLayout()
        self.assertEqual(layout.n_var, 4 * len(PARAMETER_NAMES))

    def test_decode_corner_vector_returns_four_named_corners(self) -> None:
        layout = CornerProblemLayout()
        vector = [0.0] * layout.n_var
        decoded = layout.decode(vector)
        self.assertEqual(sorted(decoded.keys()), ["w_max_l_max", "w_max_l_min", "w_min_l_max", "w_min_l_min"])
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_pymoo_problem -v
```

Expected: import failure for `CornerProblemLayout`

- [ ] **Step 3: 实现角点问题布局与 `pymoo` 问题骨架**

```python
# src/pymoo_problem.py
from __future__ import annotations

from dataclasses import dataclass

from src.parameter_bounds import PARAMETER_NAMES, parameter_bounds


CORNER_NAMES = ["w_min_l_min", "w_min_l_max", "w_max_l_min", "w_max_l_max"]


@dataclass(frozen=True)
class CornerProblemLayout:
    @property
    def n_var(self) -> int:
        return len(CORNER_NAMES) * len(PARAMETER_NAMES)

    def decode(self, vector: list[float]) -> dict[str, dict[str, float]]:
        decoded: dict[str, dict[str, float]] = {}
        index = 0
        for corner_name in CORNER_NAMES:
            decoded[corner_name] = {}
            for parameter_name in PARAMETER_NAMES:
                decoded[corner_name][parameter_name] = vector[index]
                index += 1
        return decoded

    def bounds(self) -> tuple[list[float], list[float]]:
        lower = []
        upper = []
        bounds = parameter_bounds()
        for _ in CORNER_NAMES:
            for parameter_name in PARAMETER_NAMES:
                lo, hi = bounds[parameter_name]
                lower.append(lo)
                upper.append(hi)
        return lower, upper
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_pymoo_problem -v
```

Expected: all tests `OK`

### Task 3: 实现角点 NSGA 评估与 Pareto 候选导出

**Files:**
- Modify: `src/optimizer.py`
- Modify: `src/reporting.py`
- Modify: `src/simulator.py`
- Create: `tests/test_optimizer_corner_nsga.py`

- [ ] **Step 1: 写角点目标评估失败测试**

```python
# tests/test_optimizer_corner_nsga.py
import unittest

from src.optimizer import evaluate_corner_candidate
from src.targets import MetricTarget


class CornerNsgaTests(unittest.TestCase):
    def test_evaluate_corner_candidate_returns_six_objectives(self) -> None:
        target = MetricTarget(0.14, 0.028, 1e-12, 1e-13, 0.5, 0.4, 1e-5, 1e-4)

        def simulate_fn(params):
            return {
                "vtlin_v": 0.52,
                "vtsat_v": 0.38,
                "idlin_a": 1.1e-5,
                "idsat_a": 0.9e-4,
                "idoff_a": 1.2e-12,
                "isoff_a": 1.1e-13,
            }

        result = evaluate_corner_candidate(target, {"vth0": 0.3}, simulate_fn)
        self.assertEqual(len(result), 6)
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_optimizer_corner_nsga -v
```

Expected: import failure for `evaluate_corner_candidate`

- [ ] **Step 3: 实现角点评估与 Pareto 结果写出接口**

```python
# src/optimizer.py
from src.error_metrics import summarize_point_errors


def evaluate_corner_candidate(target_row, model_params, simulate_fn) -> list[float]:
    metrics = simulate_fn(model_params)
    errors = summarize_point_errors(metrics, target_row.as_metric_dict())
    return [
        float(errors["vtlin_v"]),
        float(errors["vtsat_v"]),
        float(errors["idlin_a"]),
        float(errors["idsat_a"]),
        float(errors["idoff_a"]),
        float(errors["isoff_a"]),
    ]
```

```python
# src/reporting.py
def write_pareto_candidates(path: Path, rows: list[dict[str, float | str]]) -> None:
    write_csv_rows(path, rows)
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_optimizer_corner_nsga -v
```

Expected: all tests `OK`

### Task 4: 实现连续曲面初始化与逐器件微调

**Files:**
- Create: `src/local_tuning.py`
- Modify: `src/parameterization.py`
- Create: `tests/test_local_tuning.py`

- [ ] **Step 1: 写逐器件微调范围约束失败测试**

```python
# tests/test_local_tuning.py
import unittest

from src.local_tuning import bounded_local_box


class LocalTuningTests(unittest.TestCase):
    def test_bounded_local_box_stays_inside_global_bounds(self) -> None:
        box = bounded_local_box(
            base_params={"vth0": 0.3},
            global_bounds={"vth0": (0.1, 0.5)},
            relative_radius=0.1,
        )
        self.assertEqual(box["vth0"], (0.27, 0.33))
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_local_tuning -v
```

Expected: import failure for `bounded_local_box`

- [ ] **Step 3: 实现局部微调搜索盒与曲面初值接口**

```python
# src/local_tuning.py
from __future__ import annotations


def bounded_local_box(
    base_params: dict[str, float],
    global_bounds: dict[str, tuple[float, float]],
    relative_radius: float,
) -> dict[str, tuple[float, float]]:
    result = {}
    for name, value in base_params.items():
        lower = value * (1.0 - relative_radius)
        upper = value * (1.0 + relative_radius)
        global_lower, global_upper = global_bounds[name]
        result[name] = (max(lower, global_lower), min(upper, global_upper))
    return result
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_local_tuning -v
```

Expected: all tests `OK`

### Task 5: 实现全局再拟合与工程连续模型选择

**Files:**
- Create: `src/global_refit.py`
- Create: `tests/test_global_refit.py`
- Modify: `src/parameterization.py`

- [ ] **Step 1: 写全局再拟合输出形状失败测试**

```python
# tests/test_global_refit.py
import unittest

from src.global_refit import fit_global_parameter_plane


class GlobalRefitTests(unittest.TestCase):
    def test_fit_global_parameter_plane_returns_callable_model(self) -> None:
        samples = [
            {"w_um": 0.14, "l_um": 0.028, "vth0": 0.25},
            {"w_um": 5.4, "l_um": 2.7, "vth0": 0.45},
        ]
        model = fit_global_parameter_plane("vth0", samples)
        self.assertTrue(callable(model))
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_global_refit -v
```

Expected: import failure for `fit_global_parameter_plane`

- [ ] **Step 3: 实现低阶全局再拟合入口**

```python
# src/global_refit.py
from __future__ import annotations

import math


def fit_global_parameter_plane(parameter_name: str, samples: list[dict[str, float]]):
    points = [
        (math.log10(sample["w_um"]), math.log10(sample["l_um"]), sample[parameter_name])
        for sample in samples
    ]

    def evaluate(w_um: float, l_um: float) -> float:
        x = math.log10(w_um)
        y = math.log10(l_um)
        nearest = min(points, key=lambda item: abs(item[0] - x) + abs(item[1] - y))
        return nearest[2]

    return evaluate
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_global_refit -v
```

Expected: all tests `OK`

### Task 6: 补齐绘图模块与结果图输出

**Files:**
- Create: `src/plotting.py`
- Create: `tests/test_plotting.py`
- Modify: `src/reporting.py`

- [ ] **Step 1: 写绘图输入整形失败测试**

```python
# tests/test_plotting.py
import unittest

from src.plotting import build_metric_grid


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
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_plotting -v
```

Expected: import failure for `build_metric_grid`

- [ ] **Step 3: 实现热图/Pareto/对比图基础绘图工具**

```python
# src/plotting.py
from __future__ import annotations

import numpy as np


def build_metric_grid(rows: list[dict[str, float]], value_key: str):
    widths = sorted({row["w_um"] for row in rows})
    lengths = sorted({row["l_um"] for row in rows})
    grid = np.zeros((len(widths), len(lengths)))
    for row in rows:
        wi = widths.index(row["w_um"])
        li = lengths.index(row["l_um"])
        grid[wi, li] = row[value_key]
    return widths, lengths, grid
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_plotting -v
```

Expected: all tests `OK`

### Task 7: 组装完整校准主流程并验证真实运行

**Files:**
- Modify: `src/optimizer.py`
- Modify: `run_calibration.py`
- Modify: `pyspice_run.md`

- [ ] **Step 1: 将 `run_full_calibration()` 重构为五阶段流程**

```python
# src/optimizer.py
def run_full_calibration(target_csv_path: Path, output_dir: Path = Path("artifacts/calibration_output")) -> int:
    # 1. 读取 perturbed target CSV
    # 2. 运行 4 角点 NSGA-II，导出 pareto_candidates.csv
    # 3. 构造连续曲面初值
    # 4. 对 42 点做逐器件局部微调，导出 local_tuned_params.csv
    # 5. 做全局再拟合，导出 refitted_global_params.csv
    # 6. 对全局模型做最终精修并重评估
    # 7. 输出 calibrated_params/calibrated_metrics/error_report/summary
    # 8. 生成 pareto_front/error_heatmap/target_vs_simulated/parameter_surface/corner_comparison/local_tuning_residuals
    return 0
```

- [ ] **Step 2: 跑纯 Python 测试确保新模块接口一致**

Run:

```bash
python -m unittest \
  tests.test_objectives \
  tests.test_pymoo_problem \
  tests.test_optimizer_corner_nsga \
  tests.test_local_tuning \
  tests.test_global_refit \
  tests.test_plotting -v
```

Expected: all tests `OK`

- [ ] **Step 3: 跑完整项目测试**

Run:

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest discover -s tests -v
```

Expected: full suite `OK`

- [ ] **Step 4: 跑真实校准脚本验证输出**

Run:

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/run_calibration.py
```

Expected:

- 读取 `data/targets/virtual_mosfet_metrics_perturbed_5pct.csv`
- 生成 `artifacts/calibration_output/pareto_candidates.csv`
- 生成 `artifacts/calibration_output/local_tuned_params.csv`
- 生成 `artifacts/calibration_output/refitted_global_params.csv`
- 生成 `artifacts/calibration_output/calibrated_params.csv`
- 生成 `artifacts/calibration_output/calibrated_metrics.csv`
- 生成 `artifacts/calibration_output/calibration_error_report.csv`
- 生成 `artifacts/calibration_output/calibration_summary.md`
- 生成至少 1 张 Pareto 图、6 张误差热图和参数曲面图

- [ ] **Step 5: 更新运行说明**

在 [pyspice_run.md](/Users/dangch/Documents/new_prj/spice_automodeling/pyspice_run.md) 中明确记录：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/run_calibration.py
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest discover -s tests -v
```

并注明默认目标文件为：

```text
data/targets/virtual_mosfet_metrics_perturbed_5pct.csv
```

## Self-Review

- spec 中的五阶段流程分别映射到 Task 3、Task 4、Task 5、Task 7，没有遗漏“逐器件微调仅为中间产物”这一要求。
- 多目标聚合、Pareto 候选、工程连续再拟合和绘图输出都各自有独立任务覆盖。
- 当前计划里的代码块以最小可执行接口为主，执行期需要在 `Task 7 Step 1` 把这些接口串成真实 `pymoo` 与 PySpice 流程。
- 若执行时发现 `pymoo` 在 `spice` 环境中缺失，应先安装依赖并更新 `pyspice_run.md`，再继续。
