# Agent 指引

## Critical Project Correction

2026-04-25 确认：今天拿到并分析 `RealRaw/<date>/{extend,retract}` 之前，旧 AFM 分析不知道原始曲线实际是 retract/unloading 或未区分分支，错误地把旧曲线当作完整 approach/loading 来解释。

因此：

- `extend` 必须视为 approach/loading 主曲线。
- `retract` 必须视为 unloading/pull-off/adhesion 对照曲线。
- 旧的 “120 nN approach snap-in anomaly”、极端 approach vdW/capillary enhancement、以及从 snap/pull-off 阶段提取 JJS 本征膜力学的结论不可再作为科学依据。
- 旧分析已归档到 `archive/pre_realraw_retract_misclassified_20260425/`，只用于历史追溯，不用于当前结论。

## Active RealRaw Workflow

当前主线只使用 branch-aware RealRaw 流程：

```bash
python scripts/run_realraw_analysis.py --all
python scripts/realraw_scientific_reinterpretation.py
python scripts/stitch_deep_indentation.py
python scripts/compute_apparent_modulus.py --all
python -m pytest tests/test_realraw_analysis.py
```

当前主输出：

- `results/realraw/`
- `reports/realraw/`
- `reports/realraw/apparent_modulus/surfactant_mechanics_section.pdf`

## Scientific Boundaries

- JJS 当前科学主线：branch-separated adhesion/hysteresis。Approach/extend 吸引力约为经典 vdW+capillary 同量级；retract pull-off 才是大粘附信号。
- 深压入薄膜力学：只从 stitched deep-loading positive-force 曲线提取 model-dependent apparent modulus、apparent stiffness、power-law exponent 和 slip statistics。
- Apparent modulus 用于同一探针/同一日期内部相对比较；不要写成无条件本征 Young's modulus。
- 任何新的 AFM 分析必须先确认 branch、单位、探针半径、悬臂刚度和是否需要 cantilever correction。

## Notebook 规范

> 操作 `.ipynb` 文件时，**必须先读 `notes/nbformat.md`**。

### 何时必读

- 生成、修改、追加 Jupyter Notebook 的 `.ipynb` 文件时

### 核心规范（摘要）

| 事项 | 规范 |
|------|------|
| `.ipynb` 操作 | 禁止 `import json`，必须用 `nbformat` |
| 单 cell 执行 | **禁止全量重跑整个 notebook**。追加 cell 后，从 notebook 中按顺序 `exec` 所有 code cell 到最后一个，确保变量链完整 |
| 源码 | `.py` 是源文件，`.ipynb` 是生成产物 |
| 旧模板 | 旧 `reports/JJS_analysis.py` 已归档，不能作为当前科学模板 |
| 当前模板 | 使用 RealRaw 脚本和 `reports/realraw/` 输出 |

完整模板与示例见 **`notes/nbformat.md`**。
