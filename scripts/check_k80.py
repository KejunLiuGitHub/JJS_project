import json
data = json.load(open('results/extracted_features.json','r',encoding='utf-8'))
for r in data:
    if 'k80-linker1-paa-50nm-4000nm' in r['file']:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        break

print("\n--- k80-linker1-PFNA 500nm ---")
for r in data:
    if 'k80-linker1-PFNA-50nm-500nm' in r['file']:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        break
