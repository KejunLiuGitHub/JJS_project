# AFM 二维聚合物薄膜力学分析 — 学生使用指南

> 本指南教你如何借助 AI 编程助手（Claude Code）完成 AFM 力曲线数据的自动分析。
> **核心原则：你只需要把数据放进来，告诉 AI 一句话，剩下的交给他。**

---

## 目录

1. [环境准备](#1-环境准备)
2. [项目结构速览](#2-项目结构速览)
3. [新数据放进来怎么跑](#3-新数据放进来怎么跑)
4. [与 AI Agent 协作的工作流](#4-与-ai-agent-协作的工作流)
5. [progress.md — 你的实验日志](#5-progressmd--你的实验日志)
6. [命令速查](#6-命令速查)
7. [常见问题](#7-常见问题)

---

## 1. 环境准备

```bash
# Python 3.9+
pip install numpy scipy matplotlib pandas pyyaml pytest
```

克隆仓库后，确保在 `AFM/` 根目录下工作（不是 `JJS_project/` 里面）：

```bash
cd /path/to/AFM
python JJS_project/scripts/run_full_pipeline.py --dry-run  # 测试是否正常
```

---

## 2. 项目结构速览

```
AFM/
├── README.md                     ← 你正在看的文件
├── CLAUDE.md                     ← AI Agent 的"项目说明书"（不要删）
├── progress.md                   ← ★ 你的实验日志（每次分析会自动追加）
│
├── JJS_project/                  ← 主分析代码库
│   ├── scripts/
│   │   ├── run_full_pipeline.py              ← 一键运行全流程（入口）
│   │   ├── run_realraw_analysis.py           ← 步骤1：分支识别 + 力曲线特征提取
│   │   ├── realraw_scientific_reinterpretation.py ← 步骤2：科学量重新解释
│   │   ├── stitch_deep_indentation.py        ← 步骤3：深压入滑脱拼接
│   │   ├── compute_apparent_modulus.py       ← 步骤4：表观模量拟合
│   │   ├── generate_scientific_report.py     ← 步骤5：图表 + Markdown 报告 + progress.md
│   │   ├── cleaning.py                       ← AFM 原始数据解析与基线校正
│   │   ├── dataset_registry.py               ← ★ 数据集注册表（新数据在这里登记）
│   │   └── data_qc_gui.py                    ← 交互式数据质控
│   │
│   ├── RealRaw/                   ← ★ 把原始数据放这里
│   │   ├── YYYYMMDD/              ←   每个数据集的日期文件夹
│   │   │   ├── extend/            ←   接近段（loading）原始 .txt
│   │   │   └── retract/           ←   回撤段（unloading）原始 .txt
│   │   └── ...
│   │
│   ├── results/realraw/           ← 中间计算结果（CSV/JSON）
│   └── reports/realraw/           ← 图表 + 最终 Markdown 报告
│
└── 1umSquare/                     ← 独立的 1μm 方孔数据（NLS/linker 实验）
```

---

## 3. 新数据放进来怎么跑

### 3.1 放置原始数据

将 Bruker NanoScope 导出的 `.txt` 文件按分支放入对应目录：

```
JJS_project/RealRaw/20260615/extend/    ← 接近段文件放这里
JJS_project/RealRaw/20260615/retract/   ← 回撤段文件放这里
```

> **关键约定**：extend = 探针伸出 = approach/loading，retract = 探针缩回 = unloading/pull-off。
> 同一条曲线的 extend 和 retract 文件必须**同名**，脚本会自动配对。

### 3.2 注册数据集

在 `JJS_project/scripts/dataset_registry.py` 中添加新条目：

```python
DATASETS = {
    # ... 已有的条目 ...
    "RealRaw/20260615": {
        "sample": "你的样品名",
        "probe": "DDESP-V2",       # 或 RTESPA-150
        "k": 89.0,                 # 探针刚度 N/m
        "R": 100.0,                # 针尖半径 nm
        "pattern": "*.txt",
        "units": "nm_nN",
    },
}
```

### 3.3 一键运行

```bash
cd /path/to/AFM
python JJS_project/scripts/run_full_pipeline.py
```

输出：
- 13 张科学图表（PDF + PNG）→ `JJS_project/reports/realraw/scientific_report/`
- 完整 Markdown 报告 → `JJS_project/reports/realraw/scientific_report/afm_scientific_report.md`
- 自动追加实验日志 → `progress.md`

### 3.4 把新数据告诉 AI Agent

如果你在使用 Claude Code，只需说：

> "新数据在 RealRaw/20260615，帮我加到 dataset_registry.py 然后跑全流程"

Agent 会自动完成：登记 → 运行 → 生成报告 → 更新 progress.md。

---

## 4. 与 AI Agent 协作的工作流

### 4.1 日常工作流

```
你准备好原始数据 → 放到 RealRaw/ 下
        ↓
你告诉 AI Agent 一句话 → "新数据 20260615，跑全流程"
        ↓
AI Agent 自动执行：
  1. 注册数据集（如果还没注册）
  2. 运行 run_full_pipeline.py
  3. 生成图表 + Markdown 报告
  4. 追加一条记录到 progress.md（含讨论和文献）
        ↓
你检查 progress.md → 阅读新结果 → 补充你的判断
```

### 4.2 你可以让 AI Agent 做的事情

| 你说的话 | Agent 做的事 |
|---------|-------------|
| "跑全流程" | `python JJS_project/scripts/run_full_pipeline.py` |
| "只看 step 5，重新生成报告" | `python JJS_project/scripts/generate_scientific_report.py` |
| "帮我看下新数据里 extend snap-in 比之前大了多少" | 读取 CSV，对比 progress.md 中的历史值 |
| "progress.md 里的讨论部分加上湿度控制的分析" | 在 progress.md 最新条目中追加讨论段落 |
| "搜一下最近关于 2D COF 力学性能的文献" | 用 WebSearch 检索并总结 |
| "帮我解释为什么这次的 pull-off 力特别大" | 结合计算结果和物理机制给出分析 |

### 4.3 使用技巧

1. **先跑后问**：数据放好 → 跑全流程 → progress.md 更新后 → 再和 Agent 讨论结果。
2. **progress.md 是对话基础**：Agent 会把 progress.md 当"记忆"，用它来理解你做了哪些实验、发现了什么趋势。
3. **有问题就追问**：比如"为什么 JJS 的 retract pull-off 比 extend snap-in 大 7 倍？"Agent 会从报告和文献角度解释。
4. **一个数据集一个日期文件夹**：不要混放，否则分支配对会出错。

---

## 5. progress.md — 你的实验日志

### 5.1 它是什么

`progress.md` 是**整个项目的核心输出**。它是一本自动生成的实验日志，位于仓库根目录：

```
AFM/progress.md
```

每次运行全流程，脚本会在文件末尾自动追加一个新的章节，包含：
- 时间戳（`2026-06-04 14:30 — 自动分析 #20260604-1430`）
- 数据来源（哪些数据集被分析了）
- 关键数值结果（snap-in 力、pull-off 力、模量排序等）
- 物理讨论（机制分析、统计局限性、需要补充的实验）
- 文献参考
- 关键图表（嵌入图片链接）

### 5.2 为什么它是你要维护的文件

`progress.md` 是你的**科学对话记录**。当你和导师讨论、写论文、或者几个月后回头看数据时，它会告诉你：

- 哪次跑了哪些样品
- 发现了什么规律
- 当时的解释是什么
- 哪些结论是可靠的，哪些需要更多数据

**每次跑完流程，你应该：**

1. 打开 `progress.md`，看最新追加的条目
2. 检查自动生成的讨论是否准确
3. 必要时让 AI Agent 补充你的判断：
   > "progress.md 里最新的讨论，加上：这批样品湿度 ~45%，比 JJS 那批高，所以 pull-off 更大是合理的"
4. 把 `progress.md` 提交到 git，作为实验记录永久保存

### 5.3 手动追加内容

如果你有独立的观察或新想法，可以直接告诉 AI Agent：

> "在 progress.md 里加一条手动记录：今天换了新探针，校准值 k=92.3 N/m"

Agent 会以正确格式追加。

---

## 6. 命令速查

```bash
# 全流程（跳过已缓存的步骤）
python JJS_project/scripts/run_full_pipeline.py

# 全流程（强制重新计算所有步骤，包括生成图表）
python JJS_project/scripts/run_full_pipeline.py --force

# 预览会执行什么（不实际运行）
python JJS_project/scripts/run_full_pipeline.py --dry-run

# 只要中间计算，不要图表和报告
python JJS_project/scripts/run_full_pipeline.py --skip-figures

# 单独跑某一步
python JJS_project/scripts/run_realraw_analysis.py --all          # 步骤1
python JJS_project/scripts/realraw_scientific_reinterpretation.py # 步骤2
python JJS_project/scripts/stitch_deep_indentation.py             # 步骤3
python JJS_project/scripts/compute_apparent_modulus.py --all      # 步骤4
python JJS_project/scripts/generate_scientific_report.py          # 步骤5

# 交互式数据质控（在批量分析前手动筛数据）
python JJS_project/scripts/data_qc_gui.py --dataset RealRaw/20260409

# 运行测试
python -m pytest JJS_project/tests/ -v
```

---

## 7. 常见问题

### Q: extend 和 retract 是什么？

Bruker AFM 的一个完整力曲线周期包括两段：
- **extend（接近段）**：探针向样品表面靠近，记录的是 snap-in（跳入接触）+ loading
- **retract（回撤段）**：探针从表面离开，记录的是 unloading + pull-off（拉脱粘附）

**重要**：早期分析曾把 retract 和 extend 搞混，导致报告了错误的 ~120 nN "接近段吸附力"。正确的值是 extend snap-in ~17 nN，retract pull-off ~116 nN。这一修正已写入 CLAUDE.md，Agent 不会重复这个错误。

### Q: 为什么跑全流程时有些步骤被跳过了？

每个步骤会检查输出文件是否已存在。如果存在就跳过（节省时间）。用 `--force` 强制重跑。

### Q: 数据文件该用什么单位？

Bruker 导出通常是 nm（位移）和 nN（力）。`cleaning.py` 支持 nm/μm 和 nN/μN/pN 的自动识别。把原始 .txt 文件直接放进去就行，不要手动预处理。

### Q: 报告里的"表观模量"是杨氏模量吗？

不是。表观模量 (`E_app`) 是从 F = k₁δ + k₃δ³ 膜力学模型反算出来的相对比较量，依赖于厚度假设和模型选择。它只能做**样品间排序**（比如 PAA > PFNA > SDBS），不能直接当杨氏模量用。

### Q: 能不能用其他 AI 工具（Cursor、Copilot）？

可以。核心是 `CLAUDE.md` 里有完整的项目上下文，`progress.md` 记录分析历史。任何能读取这两个文件的 AI 工具都能理解项目。

但 Claude Code 的 Agent 模式可以**全自动执行**（从数据注册到报告生成到 progress.md 更新），其他工具可能需要你逐步骤手动引导。

---

> **最后再说一遍**：数据放好 → 告诉 AI "跑全流程" → 检查 `progress.md` → 和 AI 讨论。这就是整个工作流。
