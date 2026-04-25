import sys
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve

c = AFMForceCurve('20260415原始数据/linker1-PFPE-OH-10000nm.spm - NanoScope Analysis.txt')
print(f"force_unit='{c.force_unit}'")
print(f"first 5 force raw: {c.force[:5]}")
print(f"last 5 force raw: {c.force[-5:]}")
print(f"min raw: {c.min_force}, max raw: {c.max_force}")
