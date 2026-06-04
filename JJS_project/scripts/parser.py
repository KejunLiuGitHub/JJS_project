# -*- coding: utf-8 -*-
"""
NanoScope Analysis 力曲线数据解析器
支持纯 Python 标准库运行（无外部依赖）
如果安装了 numpy，会自动使用以提升性能
"""

import os
import re
from pathlib import Path


class AFMForceCurve:
    """单条力曲线数据容器"""
    
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filename = self.filepath.name
        
        # 实验参数（从第1行解析）
        self.instrument = None          # 仪器型号
        self.mode = None                # AFM 模式
        self.scan_size = None           # 扫描范围 (nm)
        self.piezo_displacement = None  # 压电陶瓷总位移 (nm)
        self.setpoint_force = None      # 设定下压力
        self.setpoint_unit = 'nN'       # 下压力单位
        
        # 样品参数（从第2行解析）
        self.probe_model = None         # 探针型号
        self.material = None            # 所测材料
        self.substrate = None           # 基底
        self.test_condition = None      # 测试条件说明
        self.force_unit = 'nN'          # 力数据单位
        
        # 原始数据
        self.z = []      # 压电陶瓷位置 / 位移 (nm)
        self.force = []  # 力 (nN 或 uN)
        
        # 解析
        self._parse()
    
    def _parse(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 3:
            raise ValueError(f"文件 {self.filename} 数据行数不足")
        
        # === 解析第1行：实验参数 ===
        line1 = lines[0].strip()
        self.instrument = self._extract(line1, r'实验仪器为(.+?)，')
        self.mode = self._extract(line1, r'所用模式为(.+?)，')
        
        scan_match = re.search(r'扫描范围[（(]scan size[）)]为(\d+)nm×(\d+)nm', line1)
        if scan_match:
            self.scan_size = (int(scan_match.group(1)), int(scan_match.group(2)))
        
        piezo_match = re.search(r'压电陶瓷总位移为([\d.]+)(nm|um|μm)', line1)
        if piezo_match:
            self.piezo_displacement = float(piezo_match.group(1))
        
        force_match = re.search(r'下压力为([\d.]+)(nN|uN|μN|pN)', line1)
        if force_match:
            self.setpoint_force = float(force_match.group(1))
            self.setpoint_unit = force_match.group(2)
        
        # === 解析第2行：探针/样品信息 + 列标题 ===
        line2 = lines[1].strip()
        self.probe_model = self._extract(line2, r'AFM探针型号为(.+?)，')
        self.material = self._extract(line2, r'所测材料为(.+?)，')
        self.substrate = self._extract(line2, r'基底为(.+?)，')
        
        # 检测单位：从第2行或第3行提取 z 轴单位 (nm/um) 和力单位 (nN/uN)
        # 有些文件的列标题在第2行末尾，有些在独立的第3行
        unit_lines = [line2]
        if len(lines) > 2:
            unit_lines.append(lines[2].strip())
        
        for ul in unit_lines:
            unit_match = re.search(r'(nm|um|μm)\s+(nN|uN|μN)\s*$', ul)
            if unit_match:
                self.z_unit = unit_match.group(1)
                self.force_unit = unit_match.group(2)
                break
        else:
            # 回退：逐个词匹配
            for ul in unit_lines:
                if '\t' in ul:
                    parts = ul.split('\t')
                else:
                    parts = ul.split()
                for p in parts:
                    p = p.strip()
                    if p in ('nN', 'uN', 'μN'):
                        self.force_unit = p
                    if p in ('nm', 'um', 'μm'):
                        self.z_unit = p
        
        # 默认值
        if not hasattr(self, 'z_unit') or self.z_unit is None:
            self.z_unit = 'nm'
        if not hasattr(self, 'force_unit') or self.force_unit is None:
            self.force_unit = 'nN'
        
        # === 解析数据行 ===
        data_started = False
        for line in lines[2:]:
            line = line.strip()
            if not line:
                continue
            # 跳过可能的列标题重复行
            if 'nm' in line and ('nN' in line or 'uN' in line):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                try:
                    z_val = float(parts[0])
                    f_val = float(parts[1])
                    self.z.append(z_val)
                    self.force.append(f_val)
                except ValueError:
                    continue
    
    @staticmethod
    def _extract(text, pattern):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else None
    
    def to_si_units(self):
        """将力统一转换为 nN"""
        factor = 1.0
        if self.force_unit in ('uN', 'μN'):
            factor = 1000.0
        elif self.force_unit == 'pN':
            factor = 1e-3
        return [f * factor for f in self.force]
    
    @property
    def min_force(self):
        """最小力（最负值，即最大吸引力）"""
        return min(self.force) if self.force else None
    
    @property
    def max_force(self):
        """最大力（最正值，即最大排斥力）"""
        return max(self.force) if self.force else None
    
    @property
    def snap_in_force(self):
        """跳入力（最小值，通常为负）"""
        return self.min_force
    
    @property
    def snap_in_index(self):
        """snap-in 发生的索引"""
        if not self.force:
            return None
        return self.force.index(min(self.force))
    
    @property
    def snap_in_z(self):
        """snap-in 发生的 z 位置"""
        idx = self.snap_in_index
        if idx is not None:
            return self.z[idx]
        return None
    
    def __repr__(self):
        return (f"<AFMForceCurve {self.filename}: "
                f"probe={self.probe_model}, "
                f"disp={self.piezo_displacement}nm, "
                f"setpoint={self.setpoint_force}{self.setpoint_unit}, "
                f"F_min={self.min_force:.2f}{self.force_unit}, "
                f"points={len(self.z)}>")


def load_all_curves(root_dir='.'):
    """
    递归加载目录下所有 NanoScope Analysis .txt 文件
    返回 {相对路径: AFMForceCurve} 字典
    """
    root = Path(root_dir)
    curves = {}
    for txt_file in root.rglob('*.txt'):
        # 排除根目录的 agent.md 等（如果有 .txt）
        if txt_file.name.lower() in ('agent.md', 'readme.md'):
            continue
        try:
            rel = str(txt_file.relative_to(root))
            curves[rel] = AFMForceCurve(txt_file)
        except Exception as e:
            print(f"[跳过] {txt_file}: {e}")
    return curves


def summarize(curves):
    """打印数据汇总信息"""
    print(f"共加载 {len(curves)} 条力曲线\n")
    print(f"{'文件名':<50} {'探针':<15} {'位移(nm)':<10} {'设定力':<10} {'最小力':<12} {'点数':<6}")
    print("-" * 110)
    for rel, c in sorted(curves.items()):
        print(f"{rel:<50} {str(c.probe_model):<15} {str(c.piezo_displacement):<10} "
              f"{str(c.setpoint_force)+c.setpoint_unit:<10} "
              f"{c.min_force:.2f}{c.force_unit:<6} {len(c.z):<6}")


if __name__ == '__main__':
    import json
    # 自动定位项目根目录（脚本位于 scripts/ 下）
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    curves = load_all_curves(project_root)
    summarize(curves)
    
    # 输出 JSON 元数据到 results
    meta = []
    for rel, c in curves.items():
        meta.append({
            'file': rel,
            'probe': c.probe_model,
            'material': c.material,
            'substrate': c.substrate,
            'piezo_displacement_nm': c.piezo_displacement,
            'setpoint_force': c.setpoint_force,
            'setpoint_unit': c.setpoint_unit,
            'force_unit': c.force_unit,
            'min_force': c.min_force,
            'max_force': c.max_force,
            'snap_in_z_nm': c.snap_in_z,
            'data_points': len(c.z)
        })
    
    out_path = project_root / 'results' / 'metadata.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"\n元数据已保存到 {out_path}")
