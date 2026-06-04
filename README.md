# AFM 二维聚合物薄膜力学分析

> **一句话**: 把原始数据放到指定文件夹，告诉 AI Agent "跑全流程"，结果自动写入 `progress.md`。
>
> **学生不需要手动运行任何代码。一切都通过 AI Agent 完成。**

---

## 目录

1. [项目是什么](#1-项目是什么)
2. [学生怎么用（只需 3 步）](#2-学生怎么用只需-3-步)
3. [AI Agent 会自动做什么](#3-ai-agent-会自动做什么)
4. [Git 协作流程（必读）](#4-git-协作流程必读)
5. [什么能改，什么不能改](#5-什么能改什么不能改)
6. [progress.md — 你的实验日志](#6-progressmd--你的实验日志)
7. [环境准备（一次性）](#7-环境准备一次性)

---

## 1. 项目是什么

AFM 力-距离曲线自动分析系统。原始数据来自 **Bruker NanoScope PeakForce QNM** 模式。

**分析对象**: 二维 COF (共价有机框架) 悬浮薄膜的力学性能与界面粘附。

**核心科学问题**: 超薄 COF 薄膜是否通过液桥-膜顺应性耦合放大了粘附滞后？

**三个数据集**: JJS (<10nm 非晶膜)、linker 系列 (50-80nm 结晶膜)、k80 系列 (表面活性剂对照)。

---

## 2. 学生怎么用（只需 3 步）

### 第 1 步: 把原始数据放进去

将 Bruker 导出的 `.txt` 文件按分支放入:

```
JJS_project/RealRaw/YYYYMMDD/extend/    ← 接近段 (approach)
JJS_project/RealRaw/YYYYMMDD/retract/   ← 回撤段 (retract)
```

> 同一条曲线的 extend 和 retract 文件**必须同名**，脚本自动配对。

### 第 2 步: 告诉 AI Agent

在 Claude Code 中打开本项目，说:

> "新数据在 RealRaw/20260615，帮我注册并跑全流程"

AI Agent 会自动完成一切。

### 第 3 步: 检查 progress.md

打开 `progress.md`，查看最新追加的分析结果。如果有自己的观察或判断，告诉 AI Agent:

> "在 progress.md 最新条目里补充：这批样品湿度 ~45%，pull-off 比之前大是合理的"

**你不需要手动运行任何 Python 命令。** 环境配置好以后，所有操作都通过对 AI Agent 说话完成。

---

## 3. AI Agent 会自动做什么

当你告诉 AI Agent 跑新数据时，它会按顺序执行:

| 步骤 | 脚本 | 做什么 |
|------|------|--------|
| 1 | `run_realraw_analysis.py` | 分支配对 → baseline 校正 → snap-in/contact/pull-off 检测 → 特征提取 |
| 2 | `realraw_scientific_reinterpretation.py` | 力符号校正 → 科学量换算 → 理论参考值计算 |
| 3 | `stitch_deep_indentation.py` | 深压入曲线可恢复滑脱检测与拼接 |
| 4 | `compute_apparent_modulus.py` | F = k₁δ + k₃δ³ 模型拟合 → 表观模量计算 |
| 5 | `generate_scientific_report.py` | 13 张图表 + Markdown 科学报告 + 追加 progress.md |

每一步检查缓存，已计算过的自动跳过（除非说 `--force`）。

---

## 4. Git 协作流程（必读）

### 规则

- **`main` 分支由教师维护。学生不直接 push 到 main。**
- 学生在自己的分支上工作，通过 Pull Request 申请合并。
- 教师审查后批准或拒绝。

### 学生工作流

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 创建自己的分支（用你的名字）
git checkout -b student/你的名字/做了什么

# 3. 添加新数据
cp -r /你的数据/20260615 JJS_project/RealRaw/

# 4. 告诉 AI Agent 注册数据并跑全流程（AI 会修改 dataset_registry.py + progress.md）

# 5. 提交
git add JJS_project/RealRaw/20260615/ JJS_project/scripts/dataset_registry.py progress.md
git commit -m "add: 20260615 数据, 更新 progress.md"
git push origin student/你的名字/做了什么

# 6. 在 Gitee 上创建 Pull Request，等教师审查
```

### 教师审查

教师在合并前检查:
- 数据是否正确放入 extend/retract 分支
- progress.md 条目是否完整
- 文献引用是否满足宪法标准（本地文件 + 行号）
- 是否误改了受保护文件

---

## 5. 什么能改，什么不能改

### 学生可以自由修改

| 文件/目录 | 用途 | 注意 |
|-----------|------|------|
| `JJS_project/RealRaw/` | 放新数据 | extend/retract 分支不能搞反 |
| `JJS_project/scripts/dataset_registry.py` | 注册新数据集 | 按已有格式添加 |
| `progress.md` | 添加讨论、观察、笔记 | **只能追加，不能删改。规则见第 6 节** |
| `literature/` (除 README.md) | 添加新文献 MD | 必须带行号 |

### 学生不能改（需要教师审批）

| 文件/目录 | 原因 |
|-----------|------|
| `JJS_project/scripts/*.py` (除 dataset_registry.py) | 分析逻辑，需要统一维护 |
| `CLAUDE.md` | AI Agent 的行为说明书 |
| `.claude/constitution.md` | 项目宪法 |
| `literature/README.md` | 文献库格式规范 |
| `.gitignore` | 仓库配置 |

> **这个设计保证你既能跑自己的数据，又不会误改分析核心代码。**
>
> 如果你觉得某个脚本需要改进，在 PR 描述里写清楚，教师审查后决定是否采纳。

---

## 6. progress.md — 你的实验日志

`progress.md` 是项目**最重要的文件**。它是实验笔记本、科学讨论草稿、文献笔记、与导师沟通的基础。

### 每次 AI Agent 跑完后自动追加

AI Agent 每次运行会在 `progress.md` 末尾自动追加一个新条目，包含 14 个章节:
摘要、样品参数表、方法、理论模型与公式、approach 吸引力结果、retract 粘附与滞后、样品间比较、深压入拼接、膜力学模型、表观模量排序、统计注意事项、文献比较、可提取物理量、总结与展望。

### 你可以做什么

在最新条目或任意历史条目下方**追加**你的讨论、观察、笔记。格式:

```
> **学生注 (2026-06-10):** 这批样品的湿度偏高 (~55%)，pull-off 偏大可能与此有关。
> 下次实验应在干燥氮气环境下做对照。
```

告诉 AI Agent: "帮我在 progress.md 里加一条讨论，说湿度可能影响 pull-off"，它会帮你写。

### 你不能做什么

- **不能删除**自动生成的历史条目或数据段落
- **不能修改**自动生成段中的数值、公式
- **不能修改** `## 项目概览` 部分

### 发现之前的结论有错怎么办？

**不要改动原来那条。** 在最新位置追加一个更正条目，明确指出:

```
### 2026-06-11 — 手动更正 #correction-20260611

> **更正对象**: [2026-06-04 自动分析] 第 4.2 节 JJS retract 粘附力
> **原结论**: JJS pull-off 中位数为 115.9 nN
> **更正**: 经 QC 复查，剔除第 3 对异常曲线后修正为 112.4 nN
> **影响**: 不改变"pull-off 远大于 snap-in"的定性结论
```

**每次修改都会通过 `git diff` 在 PR 中显示给教师。删改历史内容会在审查中被发现。**

---

## 7. 环境准备（一次性）

```bash
# 1. 安装依赖
pip install numpy scipy matplotlib pandas pyyaml pytest

# 2. 克隆仓库
git clone https://gitee.com/sculkj/afm_machanics.git
cd afm_machanics

# 3. 验证环境（告诉 AI Agent 就行，不用自己跑）
# "帮我 dry-run 一下看环境对不对"
```

---

## 附录: 项目文件结构速览

```
AFM/
├── README.md                     ← 你正在看的文件
├── CLAUDE.md                     ← AI Agent 的"项目说明书"
├── progress.md                   ← ★ 实验日志（核心文件）
├── .claude/constitution.md       ← 项目宪法（规则与纪律）
├── .gitignore
│
├── literature/                   ← ★ 文献库（带行号的 MD）
│   ├── README.md                 ← 文献库使用说明
│   ├── Butt_2005_SurfSciRep.md   ← AFM 力测量综述 (L001-L060)
│   ├── Lee_2008_Science.md       ← 石墨烯压入力学 (L001-L042)
│   └── ...                       ← 其他文献
│
├── JJS_project/
│   ├── scripts/                  ← 分析脚本（学生只读）
│   │   ├── run_full_pipeline.py          ← 一键全流程
│   │   ├── cleaning.py                   ← 原始数据解析
│   │   ├── dataset_registry.py           ← ★ 数据集注册（学生可改）
│   │   └── ...
│   ├── RealRaw/                  ← ★ 原始数据放这里
│   │   └── YYYYMMDD/
│   │       ├── extend/
│   │       └── retract/
│   ├── results/realraw/          ← 中间计算结果
│   ├── reports/realraw/          ← 图表 + Markdown 报告
│   └── archive/                  ← 历史归档代码
│
└── 1umSquare/                    ← 独立的 1μm 方孔实验数据
```
