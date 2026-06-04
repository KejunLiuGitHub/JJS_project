import json
data = json.load(open('results/extracted_features.json','r',encoding='utf-8'))

def fmt(val, spec):
    if val is None:
        return 'N/A'
    return format(val, spec)

# linker2-paa
print('=== linker2-paa ===')
for r in data:
    if 'linker2-paa' in r['file']:
        d = r['displacement_nm']
        s = r['snap_in_force_nN']
        cp = r['contact_z_nm']
        mx = r.get('max_force_nN', 'N/A')
        print(f"  disp={fmt(d,'>6.0f')}nm  snapin={fmt(s,'>8.2f')}nN  contact_z={fmt(cp,'>10.2f')}  maxF={mx}  {r['file']}")

print()
print('=== k80-linker1-paa ===')
for r in data:
    if 'k80-linker1-paa' in r['file']:
        d = r['displacement_nm']
        s = r['snap_in_force_nN']
        mx = r.get('max_force_nN', 'N/A')
        print(f"  disp={fmt(d,'>6.0f')}nm  snapin={fmt(s,'>8.2f')}nN  maxF={mx}  {r['file']}")

print()
print('=== k80-linker1-PFNA ===')
for r in data:
    if 'k80-linker1-PFNA' in r['file']:
        d = r['displacement_nm']
        s = r['snap_in_force_nN']
        mx = r.get('max_force_nN', 'N/A')
        sp = r['setpoint']
        print(f"  disp={fmt(d,'>6.0f')}nm  snapin={fmt(s,'>8.2f')}nN  maxF={mx}  setpoint={sp}  {r['file']}")

print()
print('=== k80-linker1-SDBS ===')
for r in data:
    if 'k80-linker1-SDBS' in r['file']:
        d = r['displacement_nm']
        s = r['snap_in_force_nN']
        mx = r.get('max_force_nN', 'N/A')
        sp = r['setpoint']
        print(f"  disp={fmt(d,'>6.0f')}nm  snapin={fmt(s,'>8.2f')}nN  maxF={mx}  setpoint={sp}  {r['file']}")
