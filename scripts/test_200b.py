# -*- coding: utf-8 -*-
"""
Build JJS_analysis.py with raw data pipeline.
This script reads the existing notebook and inserts new cells.
"""
from pathlib import Path
import inspect
import sys

ROOT = Path(__file__).parent.parent
src_path = ROOT / "reports" / "JJS_analysis.py"

# Read existing notebook
with open(src_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find insertion point
marker = 'print("Global configuration loaded'
insert_pos = content.find(marker)
if insert_pos == -1:
    print("ERROR")
    sys.exit(1)
insert_pos += len(marker)
print(f"Found marker at position {insert_pos}")
