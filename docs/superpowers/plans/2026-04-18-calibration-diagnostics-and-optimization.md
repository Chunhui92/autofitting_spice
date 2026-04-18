# Calibration Diagnostics And Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 生成一份基于当前 calibration artifacts 的中文诊断报告，并对现有优化流程做一轮低风险增强，优先提升搜索预算与漏电优先 refinement。

**Architecture:** 先读取现有 `artifacts/calibration_output/` 产物并生成诊断文档，再通过测试先行的方式扩展优化器配置与 scoring/focus 逻辑，最后在 `spice` 环境中重新运行测试和校准脚本，用新产物验证改动收益。

**Tech Stack:** Python, unittest, PySpice, scipy, pymoo, Markdown

---

## File Structure

- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `src/optimizer.py`
- Create: `artifacts/calibration_output/diagnostic_report_zh.md`
- Create: `tests/test_optimizer_strategy.py`

### Task 1: 生成中文诊断报告并同步摘要

**Files:**
- Create: `artifacts/calibration_output/diagnostic_report_zh.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: 汇总现有 artifacts 的关键结论**
- [ ] **Step 2: 写入完整中文诊断报告**
- [ ] **Step 3: 将高层摘要同步回 `AGENTS.md`**

### Task 2: 为优化策略增强写失败测试

**Files:**
- Create: `tests/test_optimizer_strategy.py`
- Modify: `src/optimizer.py`

- [ ] **Step 1: 写测试覆盖可配置预算和漏电加权 scoring**
- [ ] **Step 2: 运行新增测试，确认失败**
- [ ] **Step 3: 最小实现使测试通过**
- [ ] **Step 4: 运行新增测试，确认通过**

### Task 3: 用新策略做真实回归验证

**Files:**
- Modify: `src/optimizer.py`

- [ ] **Step 1: 在 `spice` 环境中运行全量测试**
- [ ] **Step 2: 在 `spice` 环境中重新运行校准脚本**
- [ ] **Step 3: 对比新旧 worst-case 与主导误差项**
- [ ] **Step 4: 将最终观察补充到 `AGENTS.md`**
