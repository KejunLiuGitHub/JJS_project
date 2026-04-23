import json
with open('results/extracted_features.json', encoding='utf-8') as f:
    data = json.load(f)
jjs = [r for r in data if 'JJS' in r['file']]
for r in sorted(jjs, key=lambda x: x['displacement_nm'] or 0):
    d = r['displacement_nm']
    s = r['snap_in_force_nN']
    sp = r['setpoint']
    rs = r.get('repulsive_slope_nN_per_nm')
    fname = r['file'].split('\\')[-1]
    print(f'{fname}: disp={d}nm setpoint={sp} snap={s:.1f}nN rep_slope={rs}')
