import re

with open('reports/jjs_report.typ', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Global text size
content = content.replace('#set text(font: ("New Computer Modern", "Noto Sans SC"), size: 18pt)',
                          '#set text(font: ("New Computer Modern", "Noto Sans SC"), size: 15pt)')

# 2. text(size: 16pt) -> 14pt
content = content.replace('text(size: 16pt)', 'text(size: 14pt)')

# 3. text(size: 14pt) -> 12pt (but be careful with table header and descriptions)
# We only target body text, not table headers which use 11pt already
content = content.replace('#text(size: 14pt, fill: soft)', '#text(size: 12pt, fill: soft)')
content = content.replace('#text(size: 14pt)[\n', '#text(size: 12pt)[\n')
content = content.replace('#text(size: 14pt, weight: "bold")', '#text(size: 12pt, weight: "bold")')

# 4. text(size: 13pt) -> 11pt
content = content.replace('text(size: 13pt)', 'text(size: 11pt)')

# 5. Reduce grid gutter
content = content.replace('gutter: 1.5em,', 'gutter: 1em,')

# 6. Reduce rect inset
content = content.replace('inset: 12pt)', 'inset: 8pt)')
content = content.replace('inset: 10pt)', 'inset: 7pt)')

# 7. Reduce v-space
content = content.replace('#v(1em)', '#v(0.5em)')
content = content.replace('#v(0.5em)', '#v(0.3em)')
content = content.replace('#v(0.3em)\n#v(0.3em)', '#v(0.3em)')

# 8. Reduce box heights in diagrams
content = content.replace('height: 6cm', 'height: 5cm')

with open('reports/jjs_report.typ', 'w', encoding='utf-8') as f:
    f.write(content)
print('Font size and spacing fixes applied')
