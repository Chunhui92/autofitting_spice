## 运行环境处理

- 已在代码中绑定 Homebrew 安装的 `libngspice.dylib`，让 conda `spice` 环境下的 PySpice 可以正确加载 ngspice 动态库。
- 推荐所有带 matplotlib 的命令都显式带上 `MPLCONFIGDIR=/tmp/mplconfig`，避免字体缓存写到用户目录失败。
- 推荐优先使用 `scripts/` 下的入口脚本；根目录脚本 `run_calibration.py` 和 `bsim4_dataset.py` 仅作为兼容包装保留。

## 当前目录结构

- 核心代码：[/Users/dangch/Documents/new_prj/spice_automodeling/src/calibration](/Users/dangch/Documents/new_prj/spice_automodeling/src/calibration)
- 脚本入口：[/Users/dangch/Documents/new_prj/spice_automodeling/scripts](/Users/dangch/Documents/new_prj/spice_automodeling/scripts)
- 目标数据：[/Users/dangch/Documents/new_prj/spice_automodeling/data/targets](/Users/dangch/Documents/new_prj/spice_automodeling/data/targets)
- 运行产物：[/Users/dangch/Documents/new_prj/spice_automodeling/artifacts](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts)
- 单元测试：[/Users/dangch/Documents/new_prj/spice_automodeling/tests](/Users/dangch/Documents/new_prj/spice_automodeling/tests)

## 常用运行命令

- 激活 conda 环境：

```bash
conda activate spice
```

- 生成虚拟 BSIM4 数据集：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/generate_bsim4_dataset.py
```

- 指定输出目录生成数据集：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/generate_bsim4_dataset.py --output-dir artifacts/dataset_generation
```

- 运行连续校准脚本：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/run_calibration.py
```

- 显示真实仿真日志运行校准：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run --no-capture-output -n spice python scripts/run_calibration.py
```

- 指定目标文件和输出目录运行校准：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python scripts/run_calibration.py --target-csv data/targets/virtual_mosfet_metrics_perturbed_5pct.csv --output-dir artifacts/calibration_output
```

- 运行校准相关核心测试：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest tests.test_optimizer_corner_nsga tests.test_local_tuning -v
```

- 运行当前项目全量测试：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest discover -s tests -v
```

## 当前校准状态

- 默认目标文件：[virtual_mosfet_metrics_perturbed_5pct.csv](/Users/dangch/Documents/new_prj/spice_automodeling/data/targets/virtual_mosfet_metrics_perturbed_5pct.csv)
- 当前主入口：[run_calibration.py](/Users/dangch/Documents/new_prj/spice_automodeling/scripts/run_calibration.py)
- 当前输出目录：[artifacts/calibration_output](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output)
- 当前 worst-case 相对误差约为 `5.116035e-02`
- 当前尚未满足“全部点全部指标 `<3%`”的验收门槛

## 主要输出文件

- 校准摘要：[calibration_summary.md](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/calibration_summary.md)
- 误差报告：[calibration_error_report.csv](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/calibration_error_report.csv)
- Pareto 候选：[pareto_candidates.csv](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/pareto_candidates.csv)
- 局部微调参数：[local_tuned_params.csv](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/local_tuned_params.csv)
- 全局再拟合参数：[refitted_global_params.csv](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/refitted_global_params.csv)
- 最终参数：[calibrated_params.csv](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/calibrated_params.csv)
- 最终指标：[calibrated_metrics.csv](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/calibrated_metrics.csv)
- 敏感性报告：[sensitivity_report.csv](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/sensitivity_report.csv)
- Pareto 图：[pareto_front.png](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/pareto_front.png)

## 数据集输出文件

- 参数 CSV：[/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/dataset_generation/virtual_mosfet_params.csv](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/dataset_generation/virtual_mosfet_params.csv)
- 指标 CSV：[/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/dataset_generation/virtual_mosfet_metrics.csv](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/dataset_generation/virtual_mosfet_metrics.csv)
- 宽度趋势图：[/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/dataset_generation/metrics_vs_w.png](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/dataset_generation/metrics_vs_w.png)
- 长度趋势图：[/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/dataset_generation/metrics_vs_l.png](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/dataset_generation/metrics_vs_l.png)
