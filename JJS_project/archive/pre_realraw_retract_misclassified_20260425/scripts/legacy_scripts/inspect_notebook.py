# -*- coding: utf-8 -*-
from pathlib import Path

src = Path("reports/JJS_analysis.py")
with open(src, "r", encoding="utf-8") as f:
    lines = f.readlines()

insert_idx = None
for i, line in enumerate(lines):
    if "Global configuration loaded" in line:
        insert_idx = i + 1
        break

print(f"Insertion point: line {insert_idx}")
print(f"Total lines: {len(lines)}")
