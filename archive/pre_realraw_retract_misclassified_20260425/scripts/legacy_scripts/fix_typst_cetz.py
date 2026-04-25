import re

with open('reports/jjs_report.typ', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace 3: Bar chart comparison (theory vs measured)
old3 = '''  #cetz.canvas(length: 1cm, {
    import cetz.draw: *
    let vals = (2.96, 7.24, 120.7)
    let labels = ("vdW", "Capillary", "Measured")
    let colors = (primary, rgb("#2ecc71"), accent)
    let bar-w = 1.5
    let gap = 0.8
    let width = 3 * (bar-w + gap) + gap
    let height = 5
    let ymax = 140
    
    line((0, 0), (width, 0), stroke: 0.5pt)
    line((0, 0), (0, height), stroke: 0.5pt)
    for i in (0, 1, 2, 3, 4, 5, 6, 7) {
      let y = i * height / 7
      line((-0.1, y), (0, y), stroke: 0.3pt)
      content((-0.4, y), [#text(size: 8pt, str(i * 20))], anchor: "east")
    }
    for (i, v) in vals.enumerate() {
      let x0 = gap + i * (bar-w + gap)
      let h = v / ymax * height
      rect((x0, 0), (x0 + bar-w, h), fill: colors.at(i))
      content((x0 + bar-w/2, -0.3), [#text(size: 9pt, weight: "bold", labels.at(i))], anchor: "north")
      content((x0 + bar-w/2, h + 0.2), [#text(size: 8pt, str(v))], anchor: "south")
    }
  })'''
new3 = '''  #bar-chart(
    ("2.96", "7.24", "120.7"),
    ("vdW", "Capillary", "Measured"),
    colors: (primary, rgb("#2ecc71"), accent),
    width: 8, height: 4, y-max: 140
  )'''
content = content.replace(old3, new3)

# Replace 4: Indentation geometry
old4 = '''      #cetz.canvas(length: 1cm, {
        import cetz.draw: *
        line((0, 0), (2, 0), stroke: 0.5pt)
        line((4, 0), (6, 0), stroke: 0.5pt)
        line((2, 0.5), (4, 0.5), stroke: primary)
        bezier((3, 0.5), (3, 1.5), (2.5, 1), (3.5, 1), stroke: accent)
        line((3, 1.5), (2.8, 2), stroke: 0.5pt)
        line((3, 1.5), (3.2, 2), stroke: 0.5pt)
        content((3, 2.2), [#text(size: 8pt)[Tip]])
        content((3, -0.3), [#text(size: 8pt)[Pore]])
      })'''
new4 = '''      #box(width: 6cm, height: 3cm)[
        #place(dx: 0cm, dy: 0cm)[#line(length: 2cm, stroke: 0.5pt)]
        #place(dx: 4cm, dy: 0cm)[#line(length: 2cm, stroke: 0.5pt)]
        #place(dx: 2cm, dy: 0.5cm)[#line(length: 2cm, stroke: primary)]
        #place(dx: 2.5cm, dy: 0.5cm)[#polygon(fill: none, stroke: accent, (0.5cm, 0cm), (0cm, 1cm), (1cm, 1cm))]
        #place(dx: 2.8cm, dy: 1.5cm)[#line(length: 0.4cm, angle: 90deg, stroke: 0.5pt)]
        #place(dx: 3.4cm, dy: 1.5cm)[#line(length: 0.4cm, angle: 90deg, stroke: 0.5pt)]
        #place(dx: 3cm, dy: 2.2cm)[#text(size: 8pt)[Tip]]
        #place(dx: 3cm, dy: -0.3cm)[#text(size: 8pt)[Pore]]
      ]'''
content = content.replace(old4, new4)

with open('reports/jjs_report.typ', 'w', encoding='utf-8') as f:
    f.write(content)
print('Replaced remaining 2 diagrams')
