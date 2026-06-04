# 文献库 — Literature Repository

> **宪法级规则**: 所有在 `progress.md`、报告、或 AI 对话中引用的科学论断，必须能追溯到本文件夹中的文献条目和**具体行号**。无法达到此标准的文献不被引用。

## 格式规范

每篇文献一个 `.md` 文件。文件名: `第一作者姓氏_年份_期刊缩写.md`（如 `Butt_2005_SurfSciRep.md`）。

### 必需 frontmatter

```yaml
---
title: "完整论文标题"
authors: "完整作者列表 (APA格式)"
journal: "期刊全名 年份, 卷, 页码范围"
doi: "10.xxxx/xxxxxxx"
tags: [关键词1, 关键词2]
citation_key: "Butt2005"    # 用于文中引用 \cite{Butt2005}
---
```

### 正文格式

- 每行以行号开头: `L001`, `L002`, ...
- 尽量保持原文结构（摘要 → 引言 → 方法 → 结果 → 讨论 → 结论）
- 在关键公式、数据、结论旁标注原文页码
- 中文翻译和原文可以并存，以 "> EN:" 标记原文

```
L001 # 摘要
L002 本文综述了原子力显微镜在力测量中的技术、解释和应用。
L003 > EN: This review article summarizes the technique, interpretation, and application of AFM force measurements.
```

## 如何添加新文献

### 方法 1: 从 PDF 转换（推荐）

```bash
# 1. 将 PDF 放入 literature/pdfs/（不被 git 追踪）
# 2. 使用 AI agent 转换:
#    "帮我把 literature/pdfs/butt2005.pdf 转成 literature/Butt_2005_SurfSciRep.md，
#     保持原文行号，中文翻译关键段落"
```

### 方法 2: 手动录入

直接创建 `.md` 文件，遵循上述格式。

## 引用规则

在 `progress.md` 或报告中引用文献时，必须包含:
1. 引用键 `[AuthorYear]`
2. 本地文件路径 `literature/Butt_2005_SurfSciRep.md`
3. 具体行号范围 `L120-L145`

示例:
```
根据 Butt 等人的综述 [Butt2005](literature/Butt_2005_SurfSciRep.md#L120-L145)，
毛细力在完全润湿条件下可写为 F_cap = 4πRγcosθ。
```

AI agent 在生成讨论和引用时，必须**先读取本地文献文件**，引用时标注行号，不得凭空生成引用内容。

## 当前文献清单

| 引用键 | 文件 | 主题 |
|--------|------|------|
| Butt2005 | Butt_2005_SurfSciRep.md | AFM 力测量综述 |
| Israelachvili2011 | Israelachvili_2011_IntermolecularForces.md | 分子间力与表面力 |
| Lee2008 | Lee_2008_Science.md | 石墨烯 AFM 压入力学 |
| Bertolazzi2011 | Bertolazzi_2011_ACSNano.md | MoS₂ 薄膜力学 |
| Jagiello2024 | Jagiello_2024_Gels.md | 水凝胶力学 |
| Su2016 | Su_2016_ACSMacroLett.md | 聚合物薄膜力学 |
| Liu2023 | Liu_2023_AdvSci.md | 软弹性体模量 |
| Xiong2025 | Xiong_2025_ChemSci.md | 2D COF 本征力学性能 |
