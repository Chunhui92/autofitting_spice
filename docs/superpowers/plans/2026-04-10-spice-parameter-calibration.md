# Spice 参数连续校准 Implementation Plan

> Note: 这是历史实施计划文档，已按当前仓库结构同步路径与入口；其中部分“预期失败”步骤保留了当时的执行语境，主要用于追溯实施过程。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个可测试、可扩展的 PySpice 参数校准工具，对 42 组 `W/L` 目标指标进行连续参数拟合，并验证每个指标相对误差都小于 `3%`。

**Architecture:** 先把现有单文件脚本拆成目标数据、参数配置、参数曲面、仿真评估、优化驱动和报告导出几个模块，再按“4 角点校准 -> 连续曲面初始化 -> 42 点联合校准”的顺序实现。测试优先覆盖纯数学与数据逻辑，PySpice 集成测试只保留少量关键链路。

**Tech Stack:** Python, PySpice, numpy, csv/dataclasses/pathlib, unittest, matplotlib

---

当前工作区不是 git 仓库，本计划不包含 `git commit` 步骤；如果后续补齐 `.git`，可按任务边界补做提交。

## File Structure

- Create: `src/__init__.py`
- Create: `src/targets.py`
- Create: `src/parameter_bounds.py`
- Create: `src/parameterization.py`
- Create: `src/simulator.py`
- Create: `src/error_metrics.py`
- Create: `src/sensitivity.py`
- Create: `src/optimizer.py`
- Create: `src/reporting.py`
- Create: `run_calibration.py`
- Modify: `src/dataset_generator.py`
- Modify: `pyspice_run.md`
- Create: `tests/test_targets.py`
- Create: `tests/test_parameter_bounds.py`
- Create: `tests/test_parameterization.py`
- Create: `tests/test_error_metrics.py`
- Create: `tests/test_sensitivity.py`
- Create: `tests/test_optimizer_smoke.py`

### Task 1: 搭建目标数据与误差计算骨架

**Files:**
- Create: `src/__init__.py`
- Create: `src/targets.py`
- Create: `src/error_metrics.py`
- Create: `tests/test_targets.py`
- Create: `tests/test_error_metrics.py`

- [ ] **Step 1: 写目标数据与误差计算的失败测试**

```python
# tests/test_targets.py
from pathlib import Path
import unittest

from src.targets import MetricTargetSet


class MetricTargetSetTests(unittest.TestCase):
    def test_load_targets_builds_lookup_by_size(self) -> None:
        targets = MetricTargetSet.from_csv(Path("virtual_mosfet_metrics.csv"))
        target = targets.get(0.14, 0.028)
        self.assertAlmostEqual(target.vtlin_v, 0.62795)
        self.assertEqual(len(targets.rows), 42)

    def test_missing_size_raises_key_error(self) -> None:
        targets = MetricTargetSet.from_csv(Path("virtual_mosfet_metrics.csv"))
        with self.assertRaises(KeyError):
            targets.get(9.9, 9.9)
```

```python
# tests/test_error_metrics.py
import unittest

from src.error_metrics import relative_error, summarize_point_errors


class ErrorMetricTests(unittest.TestCase):
    def test_relative_error_uses_absolute_target_denominator(self) -> None:
        self.assertAlmostEqual(relative_error(103.0, 100.0), 0.03)
        self.assertAlmostEqual(relative_error(97.0, 100.0), 0.03)

    def test_summarize_point_errors_returns_worst_metric(self) -> None:
        errors = summarize_point_errors(
            simulated={"vtlin_v": 0.515, "idsat_a": 1.07e-4},
            target={"vtlin_v": 0.5, "idsat_a": 1.0e-4},
        )
        self.assertEqual(errors["worst_metric"], "idsat_a")
        self.assertGreater(errors["worst_relative_error"], 0.06)
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_targets tests.test_error_metrics -v
```

Expected: `ModuleNotFoundError: No module named 'calibration'`

- [ ] **Step 3: 实现最小数据装载与误差计算代码**

```python
# src/targets.py
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MetricTarget:
    w_um: float
    l_um: float
    idoff_a: float
    isoff_a: float
    vtlin_v: float
    vtsat_v: float
    idlin_a: float
    idsat_a: float


class MetricTargetSet:
    def __init__(self, rows: list[MetricTarget]) -> None:
        self.rows = rows
        self._by_size = {(row.w_um, row.l_um): row for row in rows}

    @classmethod
    def from_csv(cls, path: Path) -> "MetricTargetSet":
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = [
                MetricTarget(**{key: float(value) for key, value in row.items()})
                for row in reader
            ]
        return cls(rows)

    def get(self, w_um: float, l_um: float) -> MetricTarget:
        return self._by_size[(w_um, l_um)]
```

```python
# src/error_metrics.py
from __future__ import annotations


def relative_error(simulated: float, target: float) -> float:
    return abs(simulated - target) / abs(target)


def summarize_point_errors(simulated: dict[str, float], target: dict[str, float]) -> dict[str, float | str]:
    relative = {name: relative_error(simulated[name], target[name]) for name in target}
    worst_metric = max(relative, key=relative.get)
    return {
        "worst_metric": worst_metric,
        "worst_relative_error": relative[worst_metric],
        **relative,
    }
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_targets tests.test_error_metrics -v
```

Expected: all tests `OK`

### Task 2: 提取参数边界与可调参数向量

**Files:**
- Create: `src/parameter_bounds.py`
- Create: `tests/test_parameter_bounds.py`
- Modify: `src/dataset_generator.py`

- [ ] **Step 1: 写参数范围与默认值的失败测试**

```python
# tests/test_parameter_bounds.py
import unittest

from src.parameter_bounds import PARAMETER_NAMES, default_parameter_guess, parameter_bounds


class ParameterBoundsTests(unittest.TestCase):
    def test_parameter_names_match_expected_order(self) -> None:
        self.assertEqual(
            PARAMETER_NAMES,
            [
                "toxe", "vth0", "u0", "vsat", "rdsw", "nfactor", "eta0",
                "cit", "voff", "k2", "ub", "uc", "a0", "keta",
            ],
        )

    def test_default_guess_is_within_bounds(self) -> None:
        guess = default_parameter_guess()
        bounds = parameter_bounds()
        for name in PARAMETER_NAMES:
            lower, upper = bounds[name]
            self.assertGreaterEqual(guess[name], lower)
            self.assertLessEqual(guess[name], upper)
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_parameter_bounds -v
```

Expected: `ModuleNotFoundError` or import failure for `parameter_bounds`

- [ ] **Step 3: 实现参数范围模块，并让现有脚本复用**

```python
# src/parameter_bounds.py
from __future__ import annotations

PARAMETER_NAMES = [
    "toxe", "vth0", "u0", "vsat", "rdsw", "nfactor", "eta0",
    "cit", "voff", "k2", "ub", "uc", "a0", "keta",
]


def parameter_bounds() -> dict[str, tuple[float, float]]:
    return {
        "toxe": (0.8e-9, 1.4e-9),
        "vth0": (0.15, 0.8),
        "u0": (150.0, 900.0),
        "vsat": (5.0e4, 1.8e5),
        "rdsw": (50.0, 400.0),
        "nfactor": (0.8, 2.0),
        "eta0": (0.0, 0.15),
        "cit": (1.0e-5, 3.0e-4),
        "voff": (-0.35, 0.05),
        "k2": (-0.1, 0.15),
        "ub": (1.0e-19, 1.0e-17),
        "uc": (-0.08, 0.02),
        "a0": (0.2, 2.0),
        "keta": (-0.1, 0.05),
    }


def default_parameter_guess() -> dict[str, float]:
    bounds = parameter_bounds()
    return {name: (lower + upper) / 2.0 for name, (lower, upper) in bounds.items()}
```

```python
# src/dataset_generator.py
# 先保留原 build_model_params 的输出形式，但把 14 个参数名提取到共享模块，
# 避免后续脚本和校准器对参数顺序理解不一致。
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_parameter_bounds -v
```

Expected: all tests `OK`

### Task 3: 实现连续参数化与角点/曲面转换

**Files:**
- Create: `src/parameterization.py`
- Create: `tests/test_parameterization.py`

- [ ] **Step 1: 写角点与双线性曲面转换的失败测试**

```python
# tests/test_parameterization.py
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
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_parameterization -v
```

Expected: import failure for `BilinearSurfaceModel`

- [ ] **Step 3: 实现角点参数对象与双线性曲面**

```python
# src/parameterization.py
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CornerParameterSet:
    w_min_l_min: dict[str, float]
    w_min_l_max: dict[str, float]
    w_max_l_min: dict[str, float]
    w_max_l_max: dict[str, float]


class BilinearSurfaceModel:
    def __init__(self, parameter_name: str, corner_values: dict[str, float], w_bounds: tuple[float, float], l_bounds: tuple[float, float]) -> None:
        self.parameter_name = parameter_name
        self.corner_values = corner_values
        self.w_bounds = w_bounds
        self.l_bounds = l_bounds

    @classmethod
    def from_corners(cls, parameter_name: str, corners: CornerParameterSet, w_bounds: tuple[float, float], l_bounds: tuple[float, float]) -> "BilinearSurfaceModel":
        return cls(
            parameter_name=parameter_name,
            corner_values={
                "w_min_l_min": corners.w_min_l_min[parameter_name],
                "w_min_l_max": corners.w_min_l_max[parameter_name],
                "w_max_l_min": corners.w_max_l_min[parameter_name],
                "w_max_l_max": corners.w_max_l_max[parameter_name],
            },
            w_bounds=w_bounds,
            l_bounds=l_bounds,
        )

    def _normalize(self, value: float, bounds: tuple[float, float]) -> float:
        lo, hi = bounds
        return (math.log10(value) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))

    def evaluate(self, w_um: float, l_um: float) -> float:
        x = self._normalize(w_um, self.w_bounds)
        y = self._normalize(l_um, self.l_bounds)
        q11 = self.corner_values["w_min_l_min"]
        q12 = self.corner_values["w_min_l_max"]
        q21 = self.corner_values["w_max_l_min"]
        q22 = self.corner_values["w_max_l_max"]
        return (1 - x) * (1 - y) * q11 + (1 - x) * y * q12 + x * (1 - y) * q21 + x * y * q22
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_parameterization -v
```

Expected: all tests `OK`

### Task 4: 抽取 PySpice 仿真评估接口并保留现有数据脚本兼容

**Files:**
- Create: `src/simulator.py`
- Modify: `src/dataset_generator.py`
- Create: `tests/test_optimizer_smoke.py`

- [ ] **Step 1: 写仿真接口的冒烟测试**

```python
# tests/test_optimizer_smoke.py
import unittest

from src.parameter_bounds import default_parameter_guess
from src.simulator import simulate_metrics_for_point


class SimulatorSmokeTests(unittest.TestCase):
    def test_simulate_metrics_for_point_returns_expected_keys(self) -> None:
        metrics = simulate_metrics_for_point(
            w_um=0.14,
            l_um=0.028,
            model_params=default_parameter_guess(),
        )
        self.assertEqual(
            sorted(metrics.keys()),
            ["idoff_a", "idlin_a", "idsat_a", "isoff_a", "vtlin_v", "vtsat_v"],
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_optimizer_smoke -v
```

Expected: import failure for `simulate_metrics_for_point`

- [ ] **Step 3: 抽取现有仿真骨架到共享模块**

```python
# src/simulator.py
from __future__ import annotations

from bsim4_dataset import configure_pyspice_runtime, simulate_transfer_measures, VDD, VLIN


def simulate_metrics_for_point(w_um: float, l_um: float, model_params: dict[str, float]) -> dict[str, float]:
    configure_pyspice_runtime()
    threshold_target = 1e-8 * (w_um / l_um)
    lin = simulate_transfer_measures(w_um, l_um, VLIN, model_params, threshold_target)
    sat = simulate_transfer_measures(w_um, l_um, VDD, model_params, threshold_target)
    return {
        "idoff_a": float(sat["idoff"]),
        "isoff_a": float(sat["isoff"]),
        "vtlin_v": float(lin["vtx"]),
        "vtsat_v": float(sat["vtx"]),
        "idlin_a": float(lin["idon"]),
        "idsat_a": float(sat["idon"]),
    }
```

```python
# src/dataset_generator.py
# 让 extract_metrics 继续工作，但内部尽量复用 simulator 层返回的 6 项指标，
# 避免后续校准器与数据脚本各自维护一套仿真流程。
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest tests.test_optimizer_smoke -v
```

Expected: smoke test `OK`

### Task 5: 实现局部敏感性分析与 4 角点校准入口

**Files:**
- Create: `src/sensitivity.py`
- Create: `src/optimizer.py`
- Create: `tests/test_sensitivity.py`

- [ ] **Step 1: 写局部敏感性分析失败测试**

```python
# tests/test_sensitivity.py
import unittest

from src.sensitivity import finite_difference_sensitivity


class SensitivityTests(unittest.TestCase):
    def test_finite_difference_sensitivity_returns_metric_map(self) -> None:
        def evaluator(params: dict[str, float]) -> dict[str, float]:
            return {"vtlin_v": params["vth0"] * 2.0, "idsat_a": params["u0"] * 1e-6}

        result = finite_difference_sensitivity(
            base_params={"vth0": 0.3, "u0": 400.0},
            parameter_steps={"vth0": 0.01, "u0": 1.0},
            evaluator=evaluator,
        )
        self.assertIn("vth0", result)
        self.assertIn("vtlin_v", result["vth0"])
        self.assertGreater(result["vth0"]["vtlin_v"], 0.0)
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python -m unittest tests.test_sensitivity -v
```

Expected: import failure for `finite_difference_sensitivity`

- [ ] **Step 3: 实现局部敏感性函数与角点校准入口**

```python
# src/sensitivity.py
from __future__ import annotations


def finite_difference_sensitivity(
    base_params: dict[str, float],
    parameter_steps: dict[str, float],
    evaluator,
) -> dict[str, dict[str, float]]:
    baseline = evaluator(base_params)
    output: dict[str, dict[str, float]] = {}
    for name, step in parameter_steps.items():
        perturbed = dict(base_params)
        perturbed[name] = perturbed[name] + step
        changed = evaluator(perturbed)
        output[name] = {
            metric: (changed[metric] - baseline[metric]) / step
            for metric in baseline
        }
    return output
```

```python
# src/optimizer.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CornerCalibrationResult:
    optimized_params: dict[str, float]
    worst_relative_error: float
    point_errors: dict[str, float]


def calibrate_corner_point(target_row, initial_params, simulate_fn):
    simulated = simulate_fn(initial_params)
    return CornerCalibrationResult(
        optimized_params=initial_params,
        worst_relative_error=1.0,
        point_errors=simulated,
    )
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python -m unittest tests.test_sensitivity -v
```

Expected: all tests `OK`

### Task 6: 实现连续曲面初始化、42 点联合校准与报告导出

**Files:**
- Modify: `src/optimizer.py`
- Create: `src/reporting.py`
- Create: `run_calibration.py`
- Modify: `pyspice_run.md`

- [ ] **Step 1: 先写执行入口的失败检查**

```python
# run_calibration.py
from src.optimizer import run_full_calibration


if __name__ == "__main__":
    raise SystemExit(run_full_calibration())
```

Run:

```bash
python scripts/run_calibration.py
```

Expected: import failure or missing `run_full_calibration`

- [ ] **Step 2: 实现联合校准与报告导出最小闭环**

```python
# src/optimizer.py
def run_full_calibration() -> int:
    # 1. 读取 42 点目标
    # 2. 运行 4 角点校准
    # 3. 由角点初始化双线性曲面
    # 4. 对曲面系数做 42 点联合优化
    # 5. 计算 worst-case relative error
    # 6. 返回 0/1 作为是否达标
    return 0
```

```python
# src/reporting.py
from __future__ import annotations

import csv
from pathlib import Path


def write_error_report(path: Path, rows: list[dict[str, float | str]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
```

- [ ] **Step 3: 用真实环境跑完整链路**

Run:

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/run_calibration.py
```

Expected:

- 生成 `calibrated_params.csv`
- 生成 `calibrated_metrics.csv`
- 生成 `calibration_error_report.csv`
- 生成 `sensitivity_report.csv`
- 控制台输出 worst-case relative error

- [ ] **Step 4: 更新运行说明**

在 [pyspice_run.md](/Users/dangch/Documents/new_prj/spice_automodeling/pyspice_run.md) 增加以下命令说明：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python /Users/dangch/Documents/new_prj/spice_automodeling/scripts/run_calibration.py
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest discover -s /Users/dangch/Documents/new_prj/spice_automodeling/tests -v
```

Expected: 文档包含“数据脚本运行”和“校准脚本运行”两套命令

## Self-Review

- 规格中的 3 个核心阶段都已映射到任务：Task 5 覆盖角点校准，Task 3 覆盖连续曲面，Task 6 覆盖 42 点联合校准。
- “局部敏感性”要求已落到 Task 5，并明确按参数扰动计算尺寸相关结果。
- “可扩展性/可测试性”要求已落到模块拆分与测试任务，没有遗漏到单文件脚本里。
- 计划中没有留 `TODO/TBD` 占位，但 Task 6 的联合优化算法仍需在执行时按实际可用库决定是自写搜索还是引入 `scipy.optimize`；如果引入新依赖，需要先更新运行文档与环境说明。
