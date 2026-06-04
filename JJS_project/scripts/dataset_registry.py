# -*- coding: utf-8 -*-
"""
Dataset Registry — 所有 AFM 力曲线数据集的集中配置。

数据来源：各数据集目录下的 readme.md 文件
- 20260409: RTESPA-150, k=7 N/m (校准后), R=8 nm, 酒石酸, 氮化硅带孔
- 20260415原始数据: RTESPA-150, k=7 N/m (校准后), R=8 nm, 二维COF, 铜网
- 20260416原始数据: DDESP-V2, k=89 N/m (校准后), R=100 nm, 二维COF, 铜网

新数据集接入时，只需在此字典中添加条目即可。
"""

DATASETS = {
    "20260409": {
        "sample_name": "JJS",
        "description": "超晶格非晶薄膜 (<10nm) on SiN pore, RTESPA-150 probe",
        "film_thickness_nm": 10,  # <10nm, 非晶薄膜
        "pore_diameter_um": 20,
        "probe_radius_nm": 8.0,
        "cantilever_stiffness_N_m": 7.0,   # RTESPA-150 校准后
        "pattern": "JJS*.txt",
        "force_unit": "nN",
        "z_unit": "nm",
        "environment": "Air ambient, RH > 60 %",
        "output_prefix": "jjs",
        "has_snap_in": True,
        "substrate": "氮化硅带孔",
        "probe_model": "RTESPA-150",
    },
    "20260415原始数据": {
        "sample_name": "linker1",
        "description": "高度结晶厚膜 (50-80nm) linker1-PFPE-OH/nls/paa on copper mesh, RTESPA-150 probe",
        "film_thickness_nm": 50,  # 50-80nm 高度结晶厚膜，PFPE-OH 可能更薄
        "pore_diameter_um": 20,
        "probe_radius_nm": 8.0,
        "cantilever_stiffness_N_m": 7.0,   # RTESPA-150 校准后
        "pattern": "linker*.txt",
        "force_unit": "nN",
        "z_unit": "nm",
        "environment": "Air ambient",
        "output_prefix": "linker1",
        "has_snap_in": False,
        "substrate": "铜网",
        "probe_model": "RTESPA-150",
    },
    "20260416原始数据": {
        "sample_name": "k80",
        "description": "高度结晶厚膜 (50-80nm) Fluorinated linker (PFNA/SDBS/paa) on copper mesh, DDESP-V2 probe",
        "film_thickness_nm": 50,  # 50-80nm 高度结晶厚膜
        "pore_diameter_um": 20,
        "probe_radius_nm": 100.0,  # DDESP-V2 金刚石涂层探针，标称 100nm
        "cantilever_stiffness_N_m": 89.0,  # DDESP-V2 校准后
        "pattern": "k80*.txt",
        "force_unit": "uN",
        "z_unit": "nm",
        "environment": "Air ambient",
        "output_prefix": "k80",
        "has_snap_in": True,
        "substrate": "铜网",
        "probe_model": "DDESP-V2",
    },
    "RealRaw/20260409": {
        "sample_name": "JJS",
        "description": "RealRaw paired extend/retract JJS on SiN pore, RTESPA-150 probe",
        "film_thickness_nm": 10,
        "pore_diameter_um": 20,
        "probe_radius_nm": 8.0,
        "cantilever_stiffness_N_m": 7.0,
        "pattern": "JJS*.txt",
        "force_unit": "nN",
        "z_unit": "nm",
        "environment": "Air ambient, RH > 60 %",
        "output_prefix": "realraw_20260409",
        "has_snap_in": True,
        "substrate": "氮化硅带孔",
        "probe_model": "RTESPA-150",
        "branches": ("extend", "retract"),
    },
    "RealRaw/20260415": {
        "sample_name": "linker",
        "description": "RealRaw paired extend/retract linker surfactant series on copper mesh, RTESPA-150 probe",
        "film_thickness_nm": 50,
        "pore_diameter_um": 20,
        "probe_radius_nm": 8.0,
        "cantilever_stiffness_N_m": 7.0,
        "pattern": "linker*.txt",
        "force_unit": "nN",
        "z_unit": "nm",
        "environment": "Air ambient",
        "output_prefix": "realraw_20260415",
        "has_snap_in": False,
        "substrate": "铜网",
        "probe_model": "RTESPA-150",
        "branches": ("extend", "retract"),
    },
    "RealRaw/20260416": {
        "sample_name": "k80",
        "description": "RealRaw paired extend/retract k80 linker/surfactant series on copper mesh, DDESP-V2 probe",
        "film_thickness_nm": 50,
        "pore_diameter_um": 20,
        "probe_radius_nm": 100.0,
        "cantilever_stiffness_N_m": 89.0,
        "pattern": "k80*.txt",
        "force_unit": "uN",
        "z_unit": "nm",
        "environment": "Air ambient",
        "output_prefix": "realraw_20260416",
        "has_snap_in": True,
        "substrate": "铜网",
        "probe_model": "DDESP-V2",
        "branches": ("extend", "retract"),
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
        print(f"       probe={v['probe_model']}, k={v['cantilever_stiffness_N_m']} N/m, R={v['probe_radius_nm']} nm")


if __name__ == "__main__":
    list_datasets()
