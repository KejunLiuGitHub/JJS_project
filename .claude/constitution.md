# 项目宪法 — Project Constitution

> 本文档定义本 AFM 力学分析项目的不可侵犯规则。AI Agent、学生、教师三方均须遵守。
> 宪法优先级高于任何单次对话中的临时指令。

---

## 第一条: progress.md 是项目的中心科学记录

### 1.1 地位
`progress.md` 是本项目**最重要的文件**。它是:
- 实验日志 (lab notebook)
- 科学讨论草稿 (discussion draft)
- 文献笔记 (literature notes)
- 结果记录 (results log)
- 与导师对话的基础 (advisor communication basis)

### 1.2 写入规则
1. 每次运行 `generate_scientific_report.py` **必须**在 `progress.md` 末尾追加新条目。
2. 每个条目必须包含: 时间戳、数据来源、关键数值结果、物理讨论、文献引用（带行号）、图表。
3. 条目不得少于以下内容: 摘要、样品参数表、方法、理论模型与公式、实验结果、物理机制讨论、统计注意事项、文献比较、总结与展望。
4. 追加，不覆盖。`progress.md` 只增不改。
5. **学生可以手动在 progress.md 中添加讨论、观察、实验笔记。** 鼓励但不强制。

### 1.3 AI Agent 的义务
1. 每次对话中如果涉及科学结果，必须先读取 `progress.md` 了解历史。
2. 生成科学论断时必须引用 `progress.md` 中的历史数据作为上下文。
3. 不得凭空编造数据或引用。所有数值必须可以追溯到 `results/` 中的 CSV 文件。

---

## 第二条: 文献引用必须引用本地文件并标注行号

### 2.1 引用的宪法标准
**任何科学引用必须满足以下三个条件，缺一不可:**

1. 被引文献存在于 `literature/` 文件夹中，是一个 `.md` 文件
2. 引用时标注了该文献在本地文件中的**具体行号范围**（如 `L020-L035`）
3. 引用内容与所标行号范围内的内容**实质一致**

**不满足以上三条件的文献，不得被引用。**

### 2.2 AI Agent 的义务
1. 在生成任何引用之前，**必须先用 Read 工具读取**对应的 `literature/*.md` 文件。
2. 引用时使用格式: `[AuthorYear](literature/File.md#Lxxx-Lxxx)`
3. 不得引用不存在于本地 `literature/` 文件夹中的文献。
4. 不得编造行号或虚构引用内容。
5. 如果客户需要的文献不在本地文献库中，AI Agent 应明确说明:
   > "[AuthorYear] 不在本地文献库中，根据宪法第二条，不能引用。建议将 PDF 放入 literature/pdfs/ 后转换为带行号的 MD。"

### 2.3 文献库维护
1. `literature/README.md` 是文献库的使用说明，不得删除。
2. 新文献通过以下流程添加:
   a. 将 PDF 放入 `literature/pdfs/`（在 .gitignore 中，不被 git 追踪）
   b. 要求 AI Agent 转换为带行号的 MD 文件
   c. 人工检查转换质量后提交到 git
3. `literature/pdfs/` 目录不提交到 git（已在 .gitignore 中配置）。

---

## 第三条: 代码与仓库纪律

### 3.1 活跃代码 vs 归档代码
1. `JJS_project/scripts/` 中的代码必须是**可以运行**的。非工作代码移入 `archive/`。
2. `archive/` 中的代码仅供历史参考，AI Agent 不将其作为当前工作流的依据。
3. 新脚本在确认跑通后才能留在 `scripts/` 中。

### 3.2 数据规则
1. 原始数据放在 `JJS_project/RealRaw/<YYYYMMDD>/extend/` 和 `retract/` 下。
2. 每批新数据必须在 `dataset_registry.py` 中注册。
3. 中间结果（CSV/JSON）由脚本自动生成，不应手动编辑。
4. 大文件 (zip、tar) 不提交到 git。

### 3.3 学生可以修改的文件
- `JJS_project/RealRaw/` — 添加新数据
- `JJS_project/scripts/dataset_registry.py` — 注册新数据集
- `progress.md` — 添加讨论、观察、笔记
- `literature/` — 添加新文献 MD 文件（不包括 README.md 的格式规范部分）

### 3.4 学生不应修改的文件（需要教师审批）
- `JJS_project/scripts/` 中除 `dataset_registry.py` 外的所有 Python 文件
- `CLAUDE.md`
- `.claude/constitution.md`
- `literature/README.md`
- `README.md`
- `.gitignore`

---

## 第四条: Git 协作流程

### 4.1 分支策略
1. `main` 分支由教师维护，学生不得直接 push 到 main。
2. 学生在新分支上工作: `student/<姓名>/<内容>` (如 `student/zhangsan/add-20260615-data`)。
3. 学生通过 Pull Request (PR) / Merge Request 申请合并到 main。
4. 教师在审查后批准或拒绝合并。

### 4.2 学生的 Git 工作流
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 创建自己的分支
git checkout -b student/<姓名>/<内容>

# 3. 添加新数据 / 修改 progress.md
# ...

# 4. 提交并推送
git add RealRaw/20260615/ dataset_registry.py progress.md
git commit -m "add: 20260615 data, update progress.md"
git push origin student/<姓名>/<内容>

# 5. 在 Gitee 上创建 Pull Request
# 教师审查后合并
```

### 4.3 教师的审查要点
1. 新数据是否正确放置在 `extend/` 和 `retract/` 下
2. progress.md 条目是否完整（14 个章节）
3. 文献引用是否满足宪法第二条
4. 是否修改了不应修改的文件
5. 数据注册是否正确

### 4.4 AI Agent 的义务
1. 当学生说"帮我提交"时，AI Agent 应引导学生在自己的分支上操作，**不应该**直接 push 到 main。
2. AI Agent 不得在学生分支上修改受保护文件（见 3.4）。
3. 如果学生要求修改受保护文件，AI Agent 应说明:
   > "这个文件需要教师审批。建议在 progress.md 或 PR 描述中说明修改原因。"

---

## 第五条: AI Agent 行为规范

### 5.1 核心原则
1. **先查后答**: 回答科学问题前，先读取 `progress.md`、相关 `results/` CSV 和 `literature/` 文件。
2. **有据可查**: 所有数值和物理论断必须有来源（progress.md、results CSV、literature 行号）。
3. **承认不确定性**: 科学结论必须标注置信度 (稳健/半定量/不可提取)。
4. **促进讨论**: 在 progress.md 讨论段中主动指出统计缺陷、缺失对照、替代解释。

### 5.2 禁止行为
1. 禁止编造文献引用或行号
2. 禁止引用不在本地 literature/ 中的文献
3. 禁止在学生分支上直接修改受保护文件
4. 禁止覆盖或删除 progress.md 的历史条目
5. 禁止在没有人工确认的情况下删除数据文件

### 5.3 报告生成
1. 每次运行 `generate_scientific_report.py` 后，progress.md 条目的 14 个章节必须全部填充。
2. 图表引用路径使用相对路径: `JJS_project/reports/realraw/scientific_report/<name>.png`
3. 报告语言: 中文为主，英文术语保留原文。

---

## 第六条: 宪法修订程序

1. 宪法的修订需要教师发起或在 PR 中由教师批准。
2. 修订后更新 `.claude/constitution.md`，并在 commit message 中说明修改原因。
3. 所有协作者在下次 pull 后自动采用新版宪法。
