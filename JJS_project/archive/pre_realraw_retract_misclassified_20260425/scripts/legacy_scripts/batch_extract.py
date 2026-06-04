# -*- coding: utf-8 -*-
"""
批量提取所有力曲线的关键参数并输出 CSV 汇总表
纯标准库实现，无需 pandas
"""

import csv
import sys
from pathlib import Path
from parser import AFMForceCurve, load_all_curves


def export_csv(curves, outpath=None):
    if outpath is None:
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        outpath = project_root / 'results' / 'summary.csv'
    """将所有曲线元数据导出为 CSV"""
    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'file', 'date_folder', 'probe', 'material', 'substrate',
        'scan_size_nm', 'piezo_displacement_nm', 'setpoint_force', 'setpoint_unit',
        'force_unit', 'data_points',
        'z_start_nm', 'z_end_nm', 'z_range_nm',
        'min_force', 'max_force', 'snap_in_z_nm',
        'has_snap_in'  # 是否出现明显的负力跳变
    ]
    
    with open(outpath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for rel, c in sorted(curves.items()):
            parts = rel.split('\\')
            date_folder = parts[0] if len(parts) > 1 else ''
            
            z_start = c.z[0] if c.z else None
            z_end = c.z[-1] if c.z else None
            z_range = z_start - z_end if z_start is not None and z_end is not None else None
            
            # 判定是否有 snap-in：最小力 < -5 nN（或等效单位）
            has_snap_in = False
            if c.min_force is not None:
                threshold = -5.0
                if c.force_unit in ('uN', 'μN'):
                    threshold = -0.005  # uN 转 nN 等效
                has_snap_in = c.min_force < threshold
            
            row = {
                'file': rel,
                'date_folder': date_folder,
                'probe': c.probe_model,
                'material': c.material,
                'substrate': c.substrate,
                'scan_size_nm': f"{c.scan_size[0]}x{c.scan_size[1]}" if c.scan_size else '',
                'piezo_displacement_nm': c.piezo_displacement,
                'setpoint_force': c.setpoint_force,
                'setpoint_unit': c.setpoint_unit,
                'force_unit': c.force_unit,
                'data_points': len(c.z),
                'z_start_nm': round(z_start, 2) if z_start else '',
                'z_end_nm': round(z_end, 2) if z_end else '',
                'z_range_nm': round(z_range, 2) if z_range is not None else '',
                'min_force': round(c.min_force, 3) if c.min_force is not None else '',
                'max_force': round(c.max_force, 3) if c.max_force is not None else '',
                'snap_in_z_nm': round(c.snap_in_z, 2) if c.snap_in_z else '',
                'has_snap_in': 'Yes' if has_snap_in else 'No'
            }
            writer.writerow(row)
    
    print(f"CSV 汇总已保存: {outpath.resolve()}")


def print_group_stats(curves):
    """按实验日期/条件分组统计"""
    groups = {}
    for rel, c in curves.items():
        folder = rel.split('\\')[0]
        if folder not in groups:
            groups[folder] = []
        groups[folder].append(c)
    
    print("\n=== 分组统计 ===")
    for folder, cs in sorted(groups.items()):
        snap_count = sum(1 for c in cs if c.min_force is not None and c.min_force < -5)
        print(f"\n[{folder}] 文件数: {len(cs)}")
        print(f"  探针型号: {set(c.probe_model for c in cs if c.probe_model)}")
        print(f"  位移范围: {min(c.piezo_displacement for c in cs if c.piezo_displacement)} - "
              f"{max(c.piezo_displacement for c in cs if c.piezo_displacement)} nm")
        print(f"  出现 snap-in 的文件: {snap_count}/{len(cs)}")
        
        # 找出最极端的 snap-in
        if snap_count > 0:
            min_all = min(c.min_force for c in cs if c.min_force is not None and c.min_force < -5)
            print(f"  最强吸引力: {min_all:.2f} nN (或等效单位)")


if __name__ == '__main__':
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    curves = load_all_curves(project_root)
    export_csv(curves)
    print_group_stats(curves)
