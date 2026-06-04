import json
d = json.load(open('results/discarded_files.json','r',encoding='utf-8'))
print(f'Total discarded: {len(d)}')
for item in d:
    print(f"  {item['reason']:40s}  {item['file']}")
