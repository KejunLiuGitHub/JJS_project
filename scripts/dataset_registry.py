# -*- coding: utf-8 -*-
"""
Dataset Registry — 所有 AFM 力曲线数据集的集中配置。

新数据集接入时，只需在此字典中添加条目即可。
"""

DATASETS = {
    "20260409": {
        "sample_name": "JJS",
        "description": "10 nm 2D COF film on SiN pore, RTESPA-150 probe",
        "film_thickness_nm": 10,
        "pore_diameter_um": 20,
        "probe_radius_nm": 8.0,
        "cantilever_stiffness_N_m": 5.0,
        "pattern": "JJS*.txt",
        "force_unit": "nN",      # 原始文件中的力单位
        "z_unit": "nm",          # 原始文件中的 Z 单位
        "environment": "Air ambient, RH > 60 %",
        "output_prefix": "jjs",
        "has_snap_in": True,     # 是否系统性地出现 snap-in
    },
    "20260415原始数据": {
        "sample_name": "linker1",
        "description": "linker1-PFPE-OH / nls / paa on copper mesh, RTESPA-150 probe",
        "film_thickness_nm": 10,
        "pore_diameter_um": 20,
        "probe_radius_nm": 8.0,
        "cantilever_stiffness_N_m": 5.0,
        "pattern": "linker*.txt",
        "force_unit": "nN",
        "z_unit": "nm",
        "environment": "Air ambient",
        "output_prefix": "linker1",
        "has_snap_in": False,    # 部分全排斥，需验证
    },
    "20260416原始数据": {
        "sample_name": "k80",
        "description": "Fluorinated linker (PFNA/SDBS/paa) on copper mesh, DDESP-V2 probe",
        "film_thickness_nm": 50,  # 文件名中有 "50nm"
        "pore_diameter_um": 20,
        "probe_radius_nm": 8.0,   # DDESP-V2 标称半径，需确认
        "cantilever_stiffness_N_m": 5.0,
        "pattern": "k80*.txt",
        "force_unit": "uN",       # 原始文件中的力单位是 uN
        "z_unit": "nm",
        "environment": "Air ambient",
        "output_prefix": "k80",
        "has_snap_in": True,
    },
}


def get_config(dataset_key):
    """获取数据集配置，支持缺失键的默认值。"""
    if dataset_key not in DATASETS:
        raise KeyError(f"Unknown dataset: {dataset_key}. Available: {list(DATASETS.keys())}")
    return DATASETS[dataset_key]


def list_datasets():
    """打印所有已注册的数据集。"""
    print("Registered datasets:")
    for k, v in DATASETS.items():
        print(f"  {k:20s} → {v['sample_name']:10s} ({v['description']})")


if __name__ == "__main__":
    list_datasets()
