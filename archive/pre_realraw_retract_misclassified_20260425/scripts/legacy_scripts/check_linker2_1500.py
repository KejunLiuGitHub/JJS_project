import sys, numpy as np
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve

c = AFMForceCurve('20260415原始数据/linker2-paa-1500nm.spm - NanoScope Analysis.txt')
print(f"z_unit={c.z_unit}, force_unit={c.force_unit}")
z = np.array(c.z)
f = np.array(c.force)
if c.z_unit in ('um','μm'):
    z = z * 1000
print(f"z range: {z.min():.2f} - {z.max():.2f} nm")
print(f"f range: {f.min():.2f} - {f.max():.2f} nN")
print(f"first 3: {list(zip(z[:3], f[:3]))}")
print(f"last 3: {list(zip(z[-3:], f[-3:]))}")

# Find min force
min_idx = np.argmin(f)
print(f"min at index {min_idx}: z={z[min_idx]:.2f}, f={f[min_idx]:.2f}")
print(f"around min: {list(zip(z[max(0,min_idx-3):min_idx+4], f[max(0,min_idx-3):min_idx+4]))}")
