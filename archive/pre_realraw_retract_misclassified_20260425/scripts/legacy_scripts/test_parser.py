import sys
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve

c = AFMForceCurve('20260416原始数据/k80-linker1-paa-50nm-4000nm-3uN - NanoScope Analysis.txt')
print(f"filename: {c.filename}")
print(f"z_unit: {c.z_unit}")
print(f"force_unit: {c.force_unit}")
print(f"setpoint: {c.setpoint_force}{c.setpoint_unit}")
print(f"min_force (raw): {c.min_force}")
print(f"max_force (raw): {c.max_force}")
print(f"min_force (nN): {min(c.to_si_units())}")
print(f"max_force (nN): {max(c.to_si_units())}")
print(f"first 3 z: {c.z[:3]}")
print(f"first 3 force (raw): {c.force[:3]}")
print(f"first 3 force (nN): {c.to_si_units()[:3]}")
