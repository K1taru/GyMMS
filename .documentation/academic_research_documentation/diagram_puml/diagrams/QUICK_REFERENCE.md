# GyMMS Diagrams v2 - Quick Reference

## 🎯 Quick Start

### Generate All Diagrams
```bash
# Windows PowerShell - manual commands
cd diagrams
dot -Tpng -Gdpi=150 use_case_diagram.dot -o output/png/use_case_diagram_v2.png
dot -Tsvg use_case_diagram.dot -o output/svg/use_case_diagram_v2.svg
dot -Tpdf use_case_diagram.dot -o output/pdf/use_case_diagram_v2.pdf
# Repeat for other diagrams...

# Linux/Mac
./generate_diagrams_v2.sh
```

## 📁 File Locations

```
output/
├── png/     ← Use for presentations
├── svg/     ← Use for documents
└── pdf/     ← Use for printing
```

## 🔍 Which Format to Use?

| Use Case | Format | Command |
|----------|--------|---------|
| PowerPoint | PNG | `output/png/*_v2.png` |
| LaTeX Paper | PDF | `output/pdf/*_v2.pdf` |
| Word Doc | SVG | `output/svg/*_v2.svg` |
| Website | SVG | `output/svg/*_v2.svg` |
| Print | PDF | `output/pdf/*_v2.pdf` |
| Email | PDF | `output/pdf/*_v2.pdf` |

## 📊 Available Diagrams

1. **use_case_diagram_v2** - Figure 3.1 (Actors & interactions)
2. **system_architecture_diagram_v2** - Figure 3.2 (3-tier architecture)
3. **deployment_infrastructure_diagram_v2** - Figure 4.1 (Docker & Raspberry Pi)
4. **database_schema_diagram_v2** - Figure 3.3 (9 tables with relationships)
5. **user_story_map_v2** - Supplementary (23 stories across 6 epics)

## ✅ Quality Specs

- **Font Sizes:** 12-16pt (body), 16-18pt (headers)
- **PNG Resolution:** 150 DPI
- **Line Thickness:** 2px
- **Spacing:** 50% more than v1
- **Total Size:** ~2.4 MB (all formats)

## 🚀 Insert Into Documents

### Markdown
```markdown
![Diagram](output/png/use_case_diagram_v2.png)
```

### LaTeX
```latex
\includegraphics[width=0.9\textwidth]{diagrams/output/pdf/use_case_diagram_v2.pdf}
```

### HTML
```html
<img src="output/svg/use_case_diagram_v2.svg" alt="Diagram">
```

## 🔧 Regenerate Single Diagram

```bash
# PNG (150 DPI)
dot -Tpng -Gdpi=150 DIAGRAM.dot -o output/png/DIAGRAM_v2.png

# SVG
dot -Tsvg DIAGRAM.dot -o output/svg/DIAGRAM_v2.svg

# PDF
dot -Tpdf DIAGRAM.dot -o output/pdf/DIAGRAM_v2.pdf
```

## 📝 v1 vs v2 Summary

| Feature | v1 | v2 |
|---------|----|----|
| Font | 9-10pt | **12-16pt** |
| PNG DPI | 96 | **150** |
| Lines | 1px | **2px** |
| Organized | ❌ | ✅ |
| Arrow Fixes | ❌ | ✅ |

## 📚 Documentation Files

- `README_v2.md` - Complete v2 guide
- `COMPARISON_v1_v2.md` - Detailed comparison
- `INDEX.md` - Diagram catalog
- `README.md` - Original guide

## 🆘 Troubleshooting

**Text still too small?** Increase fontsize in .dot files  
**Arrows wrong?** Check direction: `A -> B` means A to B  
**Need higher resolution?** Use `-Gdpi=300` for PNG  
**File too large?** Use SVG or PDF instead of PNG

## 📞 Quick Commands Cheat Sheet

```bash
# List all v2 files
ls -lh output/png/*_v2.png
ls -lh output/svg/*_v2.svg
ls -lh output/pdf/*_v2.pdf

# View PNG
open output/png/use_case_diagram_v2.png

# Check sizes
du -sh output/png output/svg output/pdf

# Generate high-res (300 DPI)
dot -Tpng -Gdpi=300 use_case_diagram.dot -o output/png/use_case_diagram_v2_hires.png
```

---

**Version:** 2.0 | **Date:** Nov 22, 2025 | **Status:** ✅ Production Ready
