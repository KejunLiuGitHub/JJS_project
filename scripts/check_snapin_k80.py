import json
data = json.load(open('results/extracted_features.json','r',encoding='utf-8'))
print("=== k80-linker1 files with snap_in ===")
for r in data:
    if 'k80-linker1' in r['file'] and r['snap_in_force_nN'] is not None:
        print(f"  {r['snap_in_force_nN']:>10.2f} nN  {r['file']}")
