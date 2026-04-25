import re

with open('reports/jjs_report.typ', 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. Hide section divider slides ────────────────────────────────
# Add <touying:hidden> to all = X. Section lines except = Outline
lines = content.split('\n')
new_lines = []
for line in lines:
    m = re.match(r'^(= [IVX]+\. .+)$', line)
    if m and 'Outline' not in line:
        line = m.group(1) + ' <touying:hidden>'
    new_lines.append(line)
content = '\n'.join(new_lines)

# ── 2. Fix data reference bug ────────────────────────────────────
content = content.replace(
    '#calc.round(float(theory-r.at(0).at(6)), digits: 1) nN. All curves show systematic negative force',
    '#calc.round(float(theory-r.at(0).at(5)), digits: 1) nN. All curves show systematic negative force'
)

# ── 3. Fix bar-chart x-labels (rotate 45°) ───────────────────────
# The old bar-chart places labels horizontally. We rotate them.
old_bar = '''  #for (i, v) in vals.enumerate() {
      let x0 = gap + i * (bar-w + gap)
      let h = v / ymax * height
      place(dx: x0 * 1cm, dy: (height - h) * 1cm)[
        #rect(width: bar-w * 1cm, height: h * 1cm, fill: colors.at(calc.rem(i, colors.len())))
      ]
      place(dx: (x0 + bar-w / 2) * 1cm, dy: height * 1cm + 0.2cm)[
        #align(center)[#text(size: 7pt, labels.at(i))]
      ]
    }'''
new_bar = '''  #for (i, v) in vals.enumerate() {
      let x0 = gap + i * (bar-w + gap)
      let h = v / ymax * height
      place(dx: x0 * 1cm, dy: (height - h) * 1cm)[
        #rect(width: bar-w * 1cm, height: h * 1cm, fill: colors.at(calc.rem(i, colors.len())))
      ]
      place(dx: (x0 + bar-w / 2) * 1cm, dy: height * 1cm + 0.1cm)[
        #align(center)[#rotate(-45deg, origin: center)[#text(size: 6pt, labels.at(i))]]
      ]
    }'''
content = content.replace(old_bar, new_bar)

# ── 4. Fix scatter-plot axis labels ──────────────────────────────
# Remove problematic y-axis label rotation; put labels in slide text instead
old_scatter = '''    #place(dx: 0cm, dy: height * 1cm)[#align(center)[#text(size: 9pt, x-label)]]
    #place(dx: -0.5cm, dy: height * 0.5 * 1cm)[#align(center)[#rotate(90deg)[#text(size: 9pt, y-label)]]]
    #place(dx: 0cm, dy: 0cm)[#line(length: width * 1cm, stroke: 0.5pt)]
    #place(dx: 0cm, dy: 0cm)[#line(angle: 90deg, length: height * 1cm, stroke: 0.5pt)]'''
new_scatter = '''    #place(dx: width * 0.5 * 1cm, dy: -0.3cm)[#align(center)[#text(size: 9pt, x-label)]]
    #place(dx: -0.3cm, dy: height * 0.5 * 1cm)[#align(center)[#text(size: 9pt, y-label)]]
    #place(dx: 0cm, dy: 0cm)[#line(length: width * 1cm, stroke: 0.5pt)]
    #place(dx: 0cm, dy: 0cm)[#line(angle: 90deg, length: height * 1cm, stroke: 0.5pt)]'''
content = content.replace(old_scatter, new_scatter)

# ── 5. Fix page 27 grid overflow ─────────────────────────────────
# The "Why Classic Theory Fails for Suspended Films" slide uses grid(1fr,1fr)
# with a box containing a polygon diagram on the right. The content might be
# too tall. Let's simplify: reduce inset, make text smaller, or change layout.
# First, let's find and fix that specific block.
old_grid = '''#grid(
  columns: (1fr, 1fr),
  gutter: 1.5em,
  [
    #text(size: 14pt)[
      *Rigid plane assumption:*
      - Tip interacts with only a small area ($approx pi a_0^2$)
      - No mechanical deformation
      - Force scales as $R$
    ]
    #v(0.5em)
    #text(size: 14pt)[
      *Suspended film reality:*
      - Attractive pressure causes *downward indentation*
      - Effective radius $R_(e f f) >> R_(t i p)$
      - Force scales as $R_(e f f)$ or even $R_(e f f)^2$
    ]
  ],
  [
    #rect(width: 100%, height: 100%, fill: rgb("#f8f9fa"), radius: 4pt, inset: 12pt)[
      #text(size: 14pt, weight: "bold")[Indentation geometry]
      #v(0.5em)
      #box(width: 6cm, height: 3cm)[
        #place(dx: 0cm, dy: 0cm)[#line(length: 2cm, stroke: 0.5pt)]
        #place(dx: 4cm, dy: 0cm)[#line(length: 2cm, stroke: 0.5pt)]
        #place(dx: 2cm, dy: 0.5cm)[#line(length: 2cm, stroke: primary)]
        #place(dx: 2.5cm, dy: 0.5cm)[#polygon(fill: none, stroke: accent, (0.5cm, 0cm), (0cm, 1cm), (1cm, 1cm))]
        #place(dx: 2.8cm, dy: 1.5cm)[#line(length: 0.4cm, angle: 90deg, stroke: 0.5pt)]
        #place(dx: 3.4cm, dy: 1.5cm)[#line(length: 0.4cm, angle: 90deg, stroke: 0.5pt)]
        #place(dx: 3cm, dy: 2.2cm)[#text(size: 8pt)[Tip]]
        #place(dx: 3cm, dy: -0.3cm)[#text(size: 8pt)[Pore]]
      ]
    ]
  ]
)'''
new_grid = '''#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #text(size: 13pt)[
      *Rigid plane assumption:*
      - Tip interacts with only a small area
      - No mechanical deformation
      - Force scales as $R$
    ]
    #v(0.3em)
    #text(size: 13pt)[
      *Suspended film reality:*
      - Attractive pressure causes *downward indentation*
      - Effective radius $R_(e f f) >> R_(t i p)$
      - Force scales as $R_(e f f)$ or even $R_(e f f)^2$
    ]
  ],
  [
    #rect(width: 100%, height: 5cm, fill: rgb("#f8f9fa"), radius: 4pt, inset: 8pt)[
      #align(center)[
        #text(size: 12pt, weight: "bold")[Indentation geometry]
        #v(0.3em)
        #box(width: 6cm, height: 3cm)[
          #place(dx: 0cm, dy: 0cm)[#line(length: 2cm, stroke: 0.5pt)]
          #place(dx: 4cm, dy: 0cm)[#line(length: 2cm, stroke: 0.5pt)]
          #place(dx: 2cm, dy: 0.5cm)[#line(length: 2cm, stroke: primary)]
          #place(dx: 2.5cm, dy: 0.5cm)[#polygon(fill: none, stroke: accent, (0.5cm, 0cm), (0cm, 1cm), (1cm, 1cm))]
          #place(dx: 2.8cm, dy: 1.5cm)[#line(length: 0.4cm, angle: 90deg, stroke: 0.5pt)]
          #place(dx: 3.4cm, dy: 1.5cm)[#line(length: 0.4cm, angle: 90deg, stroke: 0.5pt)]
          #place(dx: 3cm, dy: 2.2cm)[#text(size: 8pt)[Tip]]
          #place(dx: 3cm, dy: -0.3cm)[#text(size: 8pt)[Pore]]
        ]
      ]
    ]
  ]
)'''
content = content.replace(old_grid, new_grid)

with open('reports/jjs_report.typ', 'w', encoding='utf-8') as f:
    f.write(content)
print('Applied all fixes')
