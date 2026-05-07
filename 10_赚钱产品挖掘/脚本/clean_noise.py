#!/usr/bin/env python3
"""Clean up false positives in raw data and re-run filter"""
import json, os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with open('数据抓取/2026-05-07_raw.json') as f:
    data = json.load(f)

# Keywords that indicate NOT a product (job listings, personal finance, etc.)
noise_patterns = [
    'remote job', 'account director', 'net worth at', 'immigrant who',
    'resume', 'i\'m stuck between', 'finding it hard', 'sleep is terrible',
    'driver\'s seat', 'international break', 'never-ending vines'
]

fixed = 0
for item in data:
    desc = (item.get('description','') + ' ' + item.get('name','')).lower()
    for pat in noise_patterns:
        if pat in desc and item['has_revenue']:
            item['has_revenue'] = False
            item['mrr'] = 0
            fixed += 1
            break

# Also fix: "SOLO Indie Developer Community" - it's community, not a product, mark revenue false
for item in data:
    if 'solo' in item.get('name','').lower() and 'community' in item.get('name','').lower():
        if item['has_revenue']:
            item['has_revenue'] = False
            fixed += 1

# Fix "Remote Job" items
for item in data:
    if item.get('name','').lower().startswith('remote job'):
        item['has_revenue'] = False
        fixed += 1

with open('数据抓取/2026-05-07_raw.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Cleaned {fixed} noise items")
print(f"Total: {len(data)}, has_revenue: {sum(1 for x in data if x['has_revenue'])}, MRR>0: {sum(1 for x in data if x['mrr'] > 0)}")
