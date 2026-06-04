import sys, numpy as np
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve

c = AFMForceCurve('20260409/JJS-50nm-1000nm-50nN - NanoScope Analysis.txt')
z_raw = np.array(c.z, dtype=float)
f_raw = np.array(c.force, dtype=float)

# 反转
z = z_raw[::-1].copy()
f = f_raw[::-1].copy()

# 基线校正
mask_far = (z >= 0) & (z <= 100)
coeffs = np.polyfit(z[mask_far], f[mask_far], 1)
a, b = coeffs[0], coeffs[1]
f_corr = f - (a * z + b)

snap_idx = np.argmin(f_corr)
print(f"snap_idx={snap_idx}, z={z[snap_idx]:.2f}, f={f_corr[snap_idx]:.2f}")

after_snap = np.arange(snap_idx + 1, len(z))
cc = after_snap[f_corr[after_snap] >= 0]
if len(cc) > 0:
    ci = cc[0]
    print(f"contact_idx={ci}, z={z[ci]:.2f}, f={f_corr[ci]:.2f}")
    print("\nAll points after snap-in:")
    for i in range(snap_idx, min(len(z), snap_idx+20)):
        marker = " <-- contact" if i == ci else ""
        print(f"  i={i:3d} z={z[i]:.2f} f_raw={f[i]:.2f} f_corr={f_corr[i]:.2f}{marker}")
    
    rep = (z >= z[ci]) & (f_corr >= 0)
    print(f"\nRepulsive points: {np.sum(rep)}")
    if np.sum(rep) >= 2:
        slope = np.polyfit(z[rep], f_corr[rep], 1)[0]
        print(f"slope = {slope:.4f} nN/nm")
        
        # 检查这些点是否有异常
        rep_z = z[rep]
        rep_f = f_corr[rep]
        print("\nRepulsive region points:")
        for i in range(len(rep_z)):
            print(f"  z={rep_z[i]:.2f}, f={rep_f[i]:.2f}")
