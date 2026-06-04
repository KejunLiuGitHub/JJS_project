import sys, numpy as np
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve
from pathlib import Path

def analyze_transition(fpath):
    c = AFMForceCurve(fpath)
    z_raw = np.array(c.z, dtype=float)
    f_raw = np.array(c.force, dtype=float)
    if c.z_unit in ('um', 'μm'):
        z_raw = z_raw * 1000.0
    if c.force_unit in ('uN', 'μN'):
        f_raw = f_raw * 1000.0
    
    z = z_raw[::-1].copy()
    f = f_raw[::-1].copy()
    
    # 基线校正
    mask_far = (z >= 0) & (z <= 100)
    if np.sum(mask_far) >= 5:
        coeffs = np.polyfit(z[mask_far], f[mask_far], 1)
        a, b = coeffs[0], coeffs[1]
        f_corr = f - (a * z + b)
    else:
        f_corr = f
    
    snap_idx = int(np.argmin(f_corr))
    snap_z, snap_f = z[snap_idx], f_corr[snap_idx]
    
    after_snap = np.arange(snap_idx + 1, len(z))
    cc = after_snap[f_corr[after_snap] >= 0]
    if len(cc) > 0:
        contact_idx = int(cc[0])
        contact_z, contact_f = z[contact_idx], f_corr[contact_idx]
    else:
        contact_idx = len(z) - 1
        contact_z, contact_f = z[-1], f_corr[-1]
    
    # 过渡区：snap_idx 到 contact_idx
    trans_indices = np.arange(snap_idx, contact_idx + 1)
    trans_z = z[trans_indices]
    trans_f = f_corr[trans_indices]
    
    # 参数
    delta_z = contact_z - snap_z  # snap-in 深度
    n_trans = len(trans_indices)
    
    # 平均恢复斜率（从 snap 到 contact）
    if delta_z > 0:
        avg_slope = (contact_f - snap_f) / delta_z
    else:
        avg_slope = 0
    
    # 粘着能：积分 F dz（吸引力区域，F < 0）
    adhesion_mask = trans_f < 0
    if np.sum(adhesion_mask) > 1:
        adhesion_energy = -np.trapezoid(trans_f[adhesion_mask], trans_z[adhesion_mask])
    else:
        adhesion_energy = 0
    
    # 最大负力后的最小斜率（最陡恢复段）
    if len(trans_f) >= 3:
        local_slopes = np.diff(trans_f) / np.diff(trans_z)
        max_slope = np.max(local_slopes)
        min_slope = np.min(local_slopes)
    else:
        max_slope = min_slope = 0
    
    return {
        'file': Path(fpath).name,
        'snap_z': snap_z, 'snap_f': snap_f,
        'contact_z': contact_z, 'contact_f': contact_f,
        'delta_z': delta_z, 'n_trans': n_trans,
        'avg_slope': avg_slope,
        'adhesion_energy': adhesion_energy,
        'max_local_slope': max_slope,
        'min_local_slope': min_slope,
        'trans_z': trans_z, 'trans_f': trans_f,
    }

root = Path('20260409')
results = []
for fpath in sorted(root.glob('JJS*.txt')):
    res = analyze_transition(str(fpath))
    results.append(res)
    print(f"{res['file'][:30]:30s}  snap_depth={res['delta_z']:6.2f}nm  n_pts={res['n_trans']:3d}  "
          f"avg_slope={res['avg_slope']:7.3f}N/m  adhesion={res['adhesion_energy']:8.2f}nN·nm  "
          f"max_local_slope={res['max_local_slope']:7.3f}N/m")
