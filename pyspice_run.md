
### 运行环境处理

- 已在脚本中绑定 Homebrew 安装的 `libngspice.dylib`，让 conda `spice` 环境下的 PySpice 可以正确加载 ngspice 动态库。
- 推荐所有带 matplotlib 的命令都显式带上 `MPLCONFIGDIR=/tmp/mplconfig`，避免字体缓存写到用户目录失败。

## 常用运行命令

- 激活 conda 环境：

```bash
conda activate spice
```

- 激活环境后直接运行脚本生成数据：

```bash
MPLCONFIGDIR=/tmp/mplconfig python bsim4_dataset.py
```

- 不激活环境时的一条命令运行方式：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python bsim4_dataset.py
```

- 运行测试：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest tests/test_bsim4_dataset.py
```

- 运行校准相关核心测试：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest tests.test_optimizer_corner_nsga tests.test_local_tuning -v
```

- 运行连续校准脚本：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python run_calibration.py
```

- 运行当前项目测试：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest discover -s tests -v
```

- 当前一轮真实校准执行命令：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run --no-capture-output -n spice python run_calibration.py
```

- 当前一轮全量测试执行命令：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest discover -s tests -v
```

## 当前校准状态

- 默认目标文件：[virtual_mosfet_metrics_perturbed_5pct.csv](/Users/dangch/Documents/new_prj/spice_automodeling/virtual_mosfet_metrics_perturbed_5pct.csv)
- 当前主入口：[run_calibration.py](/Users/dangch/Documents/new_prj/spice_automodeling/run_calibration.py)
- 当前输出目录：[calibration_output](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output)
- 当前 worst-case 相对误差约为 `5.116035e-02`
- 当前尚未满足“全部点全部指标 `<3%`”的验收门槛

## 主要输出文件

- 校准摘要：[calibration_summary.md](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output/calibration_summary.md)
- 误差报告：[calibration_error_report.csv](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output/calibration_error_report.csv)
- Pareto 候选：[pareto_candidates.csv](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output/pareto_candidates.csv)
- 局部微调参数：[local_tuned_params.csv](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output/local_tuned_params.csv)
- 全局再拟合参数：[refitted_global_params.csv](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output/refitted_global_params.csv)
- 最终参数：[calibrated_params.csv](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output/calibrated_params.csv)
- 最终指标：[calibrated_metrics.csv](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output/calibrated_metrics.csv)
- 敏感性报告：[sensitivity_report.csv](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output/sensitivity_report.csv)
- Pareto 图：[pareto_front.png](/Users/dangch/Documents/new_prj/spice_automodeling/calibration_output/pareto_front.png)

## 其他文件

- 原始目标趋势图输出命令仍可通过 `bsim4_dataset.py` 生成。
- 宽度趋势图：[metrics_vs_w.png](metrics_vs_w.png)
- 长度趋势图：[metrics_vs_l.png](metrics_vs_l.png)
