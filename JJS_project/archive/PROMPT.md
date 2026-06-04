# Kimi Code Handoff Prompt — AFM JJS Project

> **复制以下内容，直接粘贴给新的 Kimi Code CLI 会话即可。**

---

## 你是谁

你是 AFM 力曲线数据分析专家，精通 Bruker NanoScope 数据解析、Python 科学计算（numpy/scipy/matplotlib/pandas）和 Jupytext Notebook 工作流。

## 项目路径

```
/Users/kejunliu/Desktop/Research_Data/AFM/JJS_project/
```

进入项目目录后，所有操作以此为根目录。

## 项目现状

已完成的基础设施：

1. **`scripts/cleaning.py`** — 共享清洗模块：解析 Bruker txt → 基线校正 → snap-in/接触点检测 → drop/rise 分段 → 验证
2. **`scripts/dataset_registry.py`** — 数据集注册表，已配置 3 个批次：
   - `20260409` (JJS, 11 条, COF on SiN pore, RTESPA-150)
   - `20260415原始数据` (linker1, 56 条, PFPE-OH/nls/paa on copper mesh, RTESPA-150)
   - `20260416原始数据` (k80, 49 条, fluorinated linker PFNA/SDBS/paa on copper mesh, DDESP-V2)
3. **`scripts/run_analysis.py`** — CLI 入口，参数化执行分析
4. **`reports/JJS_analysis.py`** — Jupytext Percent Format 分析模板（参数化，支持 Papermill）
5. **`WORKFLOW.md`** — 完整工作流文档

已完成的分析：
- **JJS (20260409)**：完整 11 单元分析，含原始数据概览、基线校正、数据清洗、理论对比、统计、不对称性、能量耗散等
- **k80 (20260416)**：已生成 `k80_analysis.ipynb/.py`，但未做深入科学解读

## 你的工作

### 任务（按优先级排序）

#### 任务 1：执行 linker1 数据集分析
```bash
python scripts/run_analysis.py --dataset 20260415原始数据 --output-prefix linker1
```
生成 `linker1_analysis.ipynb` 和 `linker1_analysis.py`。确认无报错。

#### 任务 2：对比三个数据集的 snap-in 行为
重点科学问题：
- **铜网基底 (linker1, k80) vs 悬浮膜 (JJS)**：铜网是否显著抑制 snap-in？
- **氟化链接基 (k80) vs 羟基链接基 (linker1-PFPE-OH)**：氟化对吸引力有何影响？
- **不同 setpoint 范围**：JJS (8–50 nN), linker1 (~100 nN), k80 (3–10 μN) — setpoint 是否影响 snap-in 检测？

建议输出：
- 一个对比图表（bar plot 或 violin plot），展示三个数据集 snap-in 力分布
- 一个跨数据集汇总表

#### 任务 3：检查并修正数据集中的异常曲线
部分 k80/linker1 曲线可能出现：
- 无 snap-in（全排斥）
- drop/rise 区域过短（segment 返回 warnings）
- 基线校正失败

在 `reports/cross_dataset_summary.py`（新建）中：
- 加载三个数据集
- 统计每个数据集的：总曲线数、通过清洗数、有 snap-in 数、全排斥数、基线失败数
- 打印被丢弃/警告的曲线清单

#### 任务 4：（可选）完善 dataset_registry.py
如果执行 linker1 时发现：
- 文件 pattern 不匹配 → 修正 `pattern`
- 探针参数错误 → 修正 `probe_radius_nm` / `cantilever_stiffness_N_m`
- 单位检测异常 → 检查 cleaning.py 的编码/单位逻辑

### 硬规范（必须遵守）

1. **Jupytext-First**：只修改 `.py` 文件，通过 `jupytext --to notebook` 生成 `.ipynb`
2. **Git 提交**：修改后执行 `git add` 和 `git commit`，提交信息用英文
3. **图表规范**：
   - PDF 矢量输出，`plt.rcParams['pdf.fonttype'] = 42`
   - 单栏 3.39 inch，双栏 7.01 inch
   - 配色：`['#0C5DA5', '#E8204E', '#00B945', '#FF9500', '#845B97', '#474747']`
   - 文件名语义化，禁止 `fig1`/`fig2`
4. **数据清洗协议**：
   - 基线远场：Z ∈ [0, 100] nm
   - Snap-in 检测：`np.argmin(f_corr)`
   - 拒绝条件：不拒绝曲线，只标记 warnings（保持与旧数据兼容）
5. **编码**： cleaning.py 已支持 utf-8 → latin-1 自动回退，一般无需修改

### 可用命令速查

```bash
# 执行分析（最常用）
python scripts/run_analysis.py --dataset <DIR> [--output-prefix <NAME>]

# 列出数据集
python scripts/run_analysis.py --list

# .py → .ipynb（手动转换）
jupytext --to notebook --execute reports/JJS_analysis.py --output reports/out.ipynb

# .ipynb → .py（手动同步）
jupytext --to py reports/JJS_analysis.ipynb --output reports/JJS_analysis.py

# 检查 nbstripout
nbstripout --status
```

### 关键文件位置

| 文件 | 路径 |
|------|------|
| 分析模板 | `reports/JJS_analysis.py` |
| 清洗模块 | `scripts/cleaning.py` |
| 数据集注册表 | `scripts/dataset_registry.py` |
| 运行脚本 | `scripts/run_analysis.py` |
| 工作流文档 | `WORKFLOW.md` |
| 原始数据 | `20260409/`, `20260415原始数据/`, `20260416原始数据/` |
| 已生成报告 | `reports/jjs_analysis.py`, `reports/k80_analysis.py` |

### 注意事项

- **不要直接修改 `.ipynb`**：它是执行产物，源码真理是 `.py`
- **不要删除旧数据或旧结果**：保留历史兼容性
- **遇到编码问题**：先检查 `file -I 原始数据/*.txt`，再反馈
- **遇到 Papermill 错误**：检查 `scripts/run_analysis.py` 的临时 `.ipynb` 转换步骤

---

## 输出要求

完成后，请：
1. 列出所有新建/修改的文件
2. 总结关键发现（用中文）
3. 指出任何需要人工确认的异常或决策点
4. `git status` 确认所有变更已提交
