# 项目 Notes

## 2026-04-23 — nbformat 强制规范

**问题**：之前用 `import json` 直接读写 `.ipynb` 文件，导致 cell id 丢失、output 数据结构破坏、nbformat 验证警告。

**解决方案**：以后所有 `.ipynb` 文件操作必须使用官方 `nbformat` 库。

**标准模板（追加 cell）**：

```python
import nbformat as nbf

file_path = 'path/to/notebook.ipynb'

with open(file_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

new_md = nbf.v4.new_markdown_cell(r"""## 标题

说明文字。
""")

new_code = nbf.v4.new_code_cell("""# 代码注释
print("hello")
""")

nb.cells.extend([new_md, new_code])

with open(file_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
```

**已应用**：`reports/linker1_PFPE_OH_analysis.ipynb` 的 Unit 13 已通过 nbformat 规范追加。

---

## 2026-04-24 — 只执行单个 cell，禁止全量重跑

**问题**：追加新 cell 后用 `papermill.execute_notebook` 重跑整个 notebook（41 个 cell），浪费时间且覆盖已有输出。

**解决方案**：分两种情况处理。

### 情况 A：当前 Python 会话中已有前面 cell 的变量

如果当前会话就是 notebook 的 kernel（比如 Kimi CLI 的 Python 环境中已执行过前面的 cells），直接 `exec` 新 cell：

```python
import nbformat as nbf
from io import BytesIO
import base64

file_path = 'path/to/notebook.ipynb'
with open(file_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

last_cell = nb.cells[-1]
exec(last_cell.source, globals())  # 依赖前面 cell 的变量必须已存在

# 捕获输出并写回 cell...
```

### 情况 B：当前会话没有前面 cell 的变量（最稳妥）

追加 cell 后，**从 notebook 中按顺序执行所有 code cell 到最后一个**，确保变量链完整：

```python
import nbformat as nbf
from io import BytesIO
import base64

file_path = 'path/to/notebook.ipynb'
with open(file_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

# 按顺序执行所有 code cell（包括新追加的最后一个）
for i, cell in enumerate(nb.cells):
    if cell.cell_type == 'code':
        exec(cell.source, globals())
        cell.execution_count = i + 1

# 捕获最后一个 cell 的 matplotlib 输出
last_cell = nb.cells[-1]
buf = BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
img_data = base64.b64encode(buf.read()).decode('utf-8')

last_cell.outputs = [{
    'output_type': 'display_data',
    'data': {
        'image/png': img_data,
        'text/plain': ['<Figure size ...>']
    },
    'metadata': {}
}]

with open(file_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
```

**关键判断**：
- 如果 `data`、`COLORS`、`plt` 等关键变量已经在 `globals()` 中 → 用 **情况 A**
- 如果不确定变量是否存在 → 用 **情况 B**（只执行 code cell，比 papermill 全量重跑快，因为跳过了 markdown cell 和输出校验）

**PDF 文件**：由 cell 内 `fig.savefig()` 直接生成，无需额外处理
