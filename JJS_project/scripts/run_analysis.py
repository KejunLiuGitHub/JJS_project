#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFM Analysis Workflow Runner

用法:
    python scripts/run_analysis.py --dataset 20260409
    python scripts/run_analysis.py --dataset 20260416原始数据 --output-prefix k80_analysis

参数化执行 reports/JJS_analysis.py，针对指定数据集生成完整分析报告。
"""
import argparse
import sys
from pathlib import Path

# 确保可以导入 dataset_registry
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import papermill as pm
except ImportError:
    print("[错误] 缺少 papermill。请运行: pip install papermill")
    sys.exit(1)

from dataset_registry import get_config, list_datasets
from qc_filter import get_discarded_set, summarize


def run(dataset_key, output_prefix=None, dry_run=False, pattern_override=None, sample_name_override=None):
    """执行指定数据集的分析。"""
    cfg = get_config(dataset_key)

    if output_prefix is None:
        output_prefix = cfg["output_prefix"]

    input_py = PROJECT_ROOT / "reports" / "JJS_analysis.py"
    output_nb = PROJECT_ROOT / "reports" / f"{output_prefix}_analysis.ipynb"

    if not input_py.exists():
        raise FileNotFoundError(f"Template not found: {input_py}")

    parameters = {
        "DATASET_DIR": dataset_key,
        "SAMPLE_NAME": sample_name_override if sample_name_override else cfg["sample_name"],
        "FILM_THICKNESS_NM": cfg["film_thickness_nm"],
        "PORE_DIAMETER_UM": cfg["pore_diameter_um"],
        "PROBE_RADIUS_NM": cfg["probe_radius_nm"],
        "CANTILEVER_STIFFNESS_N_M": cfg["cantilever_stiffness_N_m"],
        "FILE_PATTERN": pattern_override if pattern_override else cfg["pattern"],
        "OUTPUT_PREFIX": output_prefix,
        "ENVIRONMENT": cfg["environment"],
    }

    # Load QC decisions if available
    discarded = get_discarded_set()
    if discarded:
        print(f"[QC] Loaded {len(discarded)} discarded file(s) from qc_decisions.json")
        parameters["DISCARDED_FILES"] = list(discarded)
    else:
        parameters["DISCARDED_FILES"] = []

    print(f"Dataset:     {dataset_key}")
    print(f"Sample:      {cfg['sample_name']}")
    print(f"Description: {cfg['description']}")
    print(f"Input:       {input_py}")
    print(f"Output:      {output_nb}")
    print(f"Parameters:  {parameters}")
    print()

    if dry_run:
        print("[Dry run] 不执行 notebook。")
        return

    # Papermill 只接受 .ipynb 输入，需先用 jupytext 转换
    import tempfile
    import subprocess

    with tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False, mode="w") as tmp:
        tmp_ipynb = tmp.name

    try:
        # .py → 临时 .ipynb
        subprocess.run(
            ["jupytext", "--to", "notebook", str(input_py), "--output", tmp_ipynb],
            check=True,
            capture_output=True,
        )

        # Papermill 执行参数化 notebook
        pm.execute_notebook(
            tmp_ipynb,
            str(output_nb),
            parameters=parameters,
            kernel_name="python3",
        )
        print(f"\n✅ 完成: {output_nb}")

        # 同时生成 .py 副本（便于 Git 版本控制）
        output_py = PROJECT_ROOT / "reports" / f"{output_prefix}_analysis.py"
        subprocess.run(
            ["jupytext", "--to", "py", str(output_nb), "--output", str(output_py)],
            check=True,
            capture_output=True,
        )
        print(f"✅ 同步 .py: {output_py}")
    finally:
        Path(tmp_ipynb).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="AFM Analysis Workflow Runner")
    parser.add_argument(
        "--dataset",
        required=True,
        help="数据集目录名（如 20260409, 20260415原始数据, 20260416原始数据）",
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="输出文件名前缀（默认使用 dataset_registry 中的配置）",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有已注册的数据集",
    )
    parser.add_argument(
        "--pattern",
        default=None,
        help="覆盖文件匹配模式（如 'linker1-nls-*.txt'）",
    )
    parser.add_argument(
        "--sample-name",
        default=None,
        help="覆盖样本名称",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印参数，不执行",
    )

    args = parser.parse_args()

    if args.list:
        list_datasets()
        return

    run(args.dataset, args.output_prefix, args.dry_run, args.pattern, args.sample_name)


if __name__ == "__main__":
    main()
