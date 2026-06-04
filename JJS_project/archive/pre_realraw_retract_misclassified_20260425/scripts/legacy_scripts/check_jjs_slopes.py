import json
with open('results/extracted_features.json', encoding='utf-8') as f:
    data = json.load(f)
for r in data:
    if 'JJS' in r['file']:
        s = r.get('repulsive_slope_nN_per_nm')
        print(f"{r['file'].split('/')[-1]}: rep_slope={s}, snap={r.get('snap_in_force_nN')} nN, contact_z={r.get('contact_z_nm')}")
