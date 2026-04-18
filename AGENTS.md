# 项目进展与后续计划

## 当前状态

这个项目已经从早期的单脚本原型，演进成围绕 `src/` 组织的模块化 BSIM4 校准流程。主链路已经具备：

- 目标数据读取与按尺寸索引
- 参数边界管理与连续参数曲面抽象
- 基于 `pymoo` / `NSGA-II` 的 4 角点多目标建模
- 从角点到连续曲面的双线性初始化
- 逐器件有边界的局部微调
- 基于局部教师解的全局再拟合
- CSV / Markdown / 图表输出
- `scripts/` 下的标准入口脚本
- 覆盖大部分数学层与编排层的单元测试

项目已经不是“只有设计文档”的阶段，而是已经具备一条可运行、结构也相对清晰的校准 pipeline。

结合当前工作区和 `conda` 的 `spice` 环境来看，这条 pipeline 不只是“理论可运行”，而是已经具备真实仿真依赖、测试验证和历史产物输出三者闭环。

## 已完成能力

- `src/optimizer.py` 已经承载端到端的分阶段流程：
  角点搜索、曲面初始化、局部微调、全局再拟合、最终报表输出。
- `src/pymoo_problem.py` 已经实现 4 角点参数编码和 6 目标问题包装。
- `src/local_tuning.py` 以及 `src/optimizer.py` 里的局部精修逻辑，已经在全局初始化之上叠加了 bounded local search。
- `src/global_refit.py` 当前已经提供基于 log 空间反距离加权的全局连续模型。
- `src/reporting.py` 和 `src/plotting.py` 已经能输出校准摘要、Pareto 候选、误差热图、目标值对比图和参数曲面图。
- `README.md` 已经同步了当前仓库结构和推荐命令。

## 当前工作区已验证情况

本地已执行：

```bash
MPLCONFIGDIR=/tmp/mplconfig conda run -n spice python -m unittest discover -s tests -v
```

当前观察结果：

- 40 个测试全部通过。
- 其中包括 `tests/test_optimizer_smoke.py`，说明 `PySpice` 依赖在当前 `spice` 环境中是可用的。
- 这意味着当前仓库已经具备从纯数学层测试到真实仿真 smoke test 的完整验证能力。

因此，仓库当前不是“只有结构健康”，而是“结构健康 + 核心仿真链路可运行”的状态。

本地还确认了已有校准产物目录：

- `artifacts/calibration_output/`
- `artifacts/dataset_generation/`

说明项目已经不只是代码存在，历史上也已经实际生成过一轮完整输出。

另外，当前完整中文诊断已整理到：

- [artifacts/calibration_output/diagnostic_report_zh.md](/Users/dangch/Documents/new_prj/spice_automodeling/artifacts/calibration_output/diagnostic_report_zh.md)

## 当前已知缺口

- 最终验收目标“42 个器件 x 6 个指标全部相对误差 < 3%”还没有闭环。
- 当前 `artifacts/calibration_output/calibration_summary.md` 记录的 worst-case relative error 为 `5.103840e-02`，即约 `5.10%`。
- 误差主痛点确实仍集中在漏电相关指标，而不是文档中的泛化猜测。
- 从 `calibration_error_report.csv` 看，当前 top error 主要包括：
  `idoff_a @ (0.56, 1.5)` 约 `5.104%`，
  `idoff_a @ (0.14, 0.028)` 约 `5.096%`，
  `isoff_a @ (0.56, 1.5)` 约 `4.890%`。
- 分指标 worst-case 当前大致为：
  `idoff_a 5.104%`，
  `isoff_a 4.890%`，
  `vtlin_v 4.300%`，
  `vtsat_v 4.278%`，
  `idlin_a 4.037%`，
  `idsat_a 3.851%`。
- 当前全局再拟合模型还比较轻量。`InverseDistanceSurfaceModel` 便于落地，但还不是更强的 physics-aware 或 residual-corrected 全局模型。
- 当前局部搜索虽然已经是混合式的，但即使提升后，搜索预算也仍属于中等偏保守：
  角点 `NSGA-II` 当前默认 `pop_size=24`、`n_gen=8`，
  局部 Powell 当前默认 `maxiter=36`、`maxfev=260`，
  局部 DE 当前默认 `maxiter=20`、`popsize=10`。
- 一个重要观察是：`local_tuned_params.csv` 与 `refitted_global_params.csv` 在 42 个训练点上完全一致。
- 这说明当前 `InverseDistanceSurfaceModel` 在训练点上是直接重现局部教师解的，因此当前瓶颈更像“局部教师解还不够好”，而不是“全局 refit 又把误差拉高了”。
- 本轮策略实验结果表明：
  原始基线约为 `5.116%`，只加预算可把 worst-case 小幅改善到 `5.104%`；
  轻度和中度漏电加权分别退化到约 `5.175%` 和 `5.206%`。
- 因此，当前默认策略应优先保留“更高预算”，而不应默认开启漏电偏置。

## 建议的后续计划

优先顺序建议如下：

1. 先把“当前基线”固化成可复现实验
   使用 `spice` 环境重新运行 `scripts/run_calibration.py`，保存一份带时间戳的输出目录或摘要，避免后续调参时覆盖当前 `5.104%` 默认结果和 `5.116%` 原始对照基线。

2. 集中攻克漏电误差
   利用现有 sensitivity report 和 error report，定位对 `idoff_a`、`isoff_a` 最敏感的参数，再判断当前 14 个参数自由度是否足够。

3. 优先增加搜索预算，而不是先重写算法
   当前 `pymoo` / `NSGA-II` 流程已经打通，但角点阶段和局部 refinement 阶段预算明显偏小。
   在自研优化器之前，更值得先尝试：
   增加 NSGA 代数和种群规模，
   保留更多 Pareto 候选，
   增强局部精修预算。

4. 重点区分“训练点拟合问题”和“泛化问题”
   由于当前 `local_tuned_params.csv` 与 `refitted_global_params.csv` 在训练点上完全一致，短期优先级应放在提升局部教师解质量。
   只有当后续开始评估非训练点插值或外推稳定性时，再把全局连续模型泛化能力作为主攻方向。

5. 将漏电偏置保留为实验开关，而不是默认配置
   本轮实验表明，直接提高 `idoff_a` / `isoff_a` 权重并没有带来收益，反而让整体结果变差。
   因此后续如果继续尝试漏电优先策略，应以显式实验配置方式进行，而不是直接固化为默认行为。

6. 视效果升级全局连续模型
   如果局部教师解明显优于全局 refit 曲面，下一步杠杆点就是增强全局参数模型：
   低阶残差项、平滑正则，或 surrogate-assisted refit。

7. 最后再评估是否需要自研问题特化优化器
   如果在增加搜索预算、改进局部精修、增强全局 refit 之后仍然明显卡在 `4%` 到 `5%` 区间，再考虑针对漏电指标和尺寸分布编写问题特化的混合优化器。
   在当前阶段，直接替换掉 `pymoo` 的收益优先级并不高。

## 给后续 Agent 的实践建议

- 优先使用 `scripts/generate_bsim4_dataset.py` 和 `scripts/run_calibration.py`，兼容入口脚本只作为兜底。
- `README.md` 适合作为快速入口，`docs/superpowers/plans/*.md` 更适合当历史设计背景。
- 当前 `spice` 环境已经能跑通全量测试，因此后续修改完成后，应优先在该环境里重跑测试，而不是只跑纯 Python 单测。
- 没有在当前环境重新生成 simulator-backed 输出之前，不要直接宣称校准已经达标。
- 当前最值得关注的不是“代码能不能跑”，而是“漏电误差为什么压不下去”和“全局连续模型是否把局部可达精度损失掉了”。
