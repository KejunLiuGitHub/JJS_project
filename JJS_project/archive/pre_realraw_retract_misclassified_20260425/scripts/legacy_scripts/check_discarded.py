import json
from collections import Counter

d = json.load(open('results/discarded_files.json','r',encoding='utf-8'))
print(f'Total discarded: {len(d)}')
reasons = Counter()
for item in d:
    r = item['reason']
    if r.startswith('discarded: intercept'):
        reasons['intercept > 200'] += 1
    elif r.startswith('discarded: far-end'):
        reasons['far-end < 5'] += 1
    else:
        reasons[r] += 1
for k,v in reasons.most_common():
    print(f'  {k}: {v}')

print()
print('Top 15 intercepts:')
items = sorted(d, key=lambda x: abs(x.get('intercept',0)), reverse=True)[:15]
for item in items:
    print(f"  {abs(item['intercept']):>10.1f}  {item['file']}")
