import re

with open('reports/jjs_report.typ', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove height: 100% from rect inside grids (causes overflow)
# Replace specific patterns
content = content.replace('height: 100%, fill: rgb("#f8f9fa")', 'fill: rgb("#f8f9fa")')
content = content.replace('height: 100%, fill: rgb("#eaf2f8")', 'fill: rgb("#eaf2f8")')
content = content.replace('height: 100%, fill: rgb("#fdf2e9")', 'fill: rgb("#fdf2e9")')

with open('reports/jjs_report.typ', 'w', encoding='utf-8') as f:
    f.write(content)
print('Removed height: 100% from rects')
