# Diagram Icons

Local SVG icons used by D2 diagrams. Icons are bundled into rendered SVG output — no CDN dependency at render time.

## Diagram style

- **Main nodes:** 64×64 icon + label below (`icon-*` classes)
- **Small nodes:** 40×40 icon (`icon-sm`, evaluation dimensions)
- **Tier labels:** plain text section headers (`tier-label`)
- **Legend:** horizontal strip at bottom via `grid-rows: 1` in `_legend.d2`
- **Edges:** solid = data/API (`edge-data`), dashed = metrics/traces (`edge-metrics`)

## Re-render

```bash
make diagrams
# or ./diagrams/render.sh
```

Requires [D2 CLI](https://d2lang.com/) v0.6+. Outputs `diagrams/*.svg` and `diagrams/*.pdf`.
