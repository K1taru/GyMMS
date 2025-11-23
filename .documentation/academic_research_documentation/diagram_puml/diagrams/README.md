# GyMMS Diagrams

This directory contains Graphviz DOT files for generating system diagrams used in the academic research documentation.

## Available Diagrams

1. **Use Case Diagram** (`use_case_diagram.dot`)
   - Figure 3.1 in System Analysis
   - Shows actors (Owner, Staff, Member) and their interactions with system functions
   - Displays primary use cases, admin-only functions, and extend/include relationships

2. **System Architecture Diagram** (`system_architecture_diagram.dot`)
   - Figure 3.2 in System Analysis
   - Illustrates three-tier architecture (Presentation, Application, Data)
   - Shows Django framework structure, modular apps, and container infrastructure

3. **Deployment Infrastructure Diagram** (`deployment_infrastructure_diagram.dot`)
   - Figure 4.1 in Design & Implementation
   - Depicts Docker container architecture with Raspberry Pi 5 deployment
   - Shows Cloudflare Tunnel integration and monitoring stack

4. **Database Schema Diagram** (`database_schema_diagram.dot`)
   - Figure 3.3 in System Analysis
   - Displays all 9 database tables with fields and relationships
   - Shows foreign keys, indexes, and constraints

## Prerequisites

Install Graphviz on your system:

### Windows
```bash
# Using Chocolatey
choco install graphviz

# Or download installer from: https://graphviz.org/download/
```

### macOS
```bash
brew install graphviz
```

### Linux (Debian/Ubuntu)
```bash
sudo apt-get install graphviz
```

### Raspberry Pi OS
```bash
sudo apt-get install graphviz
```

## Generating Diagrams

### Individual Diagrams

Generate PNG images:
```bash
dot -Tpng use_case_diagram.dot -o use_case_diagram.png
dot -Tpng system_architecture_diagram.dot -o system_architecture_diagram.png
dot -Tpng deployment_infrastructure_diagram.dot -o deployment_infrastructure_diagram.png
dot -Tpng database_schema_diagram.dot -o database_schema_diagram.png
```

Generate SVG images (scalable, recommended for documents):
```bash
dot -Tsvg use_case_diagram.dot -o use_case_diagram.svg
dot -Tsvg system_architecture_diagram.dot -o system_architecture_diagram.svg
dot -Tsvg deployment_infrastructure_diagram.dot -o deployment_infrastructure_diagram.svg
dot -Tsvg database_schema_diagram.dot -o database_schema_diagram.svg
```

Generate PDF (for printing):
```bash
dot -Tpdf use_case_diagram.dot -o use_case_diagram.pdf
dot -Tpdf system_architecture_diagram.dot -o system_architecture_diagram.pdf
dot -Tpdf deployment_infrastructure_diagram.dot -o deployment_infrastructure_diagram.pdf
dot -Tpdf database_schema_diagram.dot -o database_schema_diagram.pdf
```

### All Diagrams at Once

Use the provided generation script:

**Windows (PowerShell):**
```bash
./generate_diagrams.ps1
```

**Linux/macOS/Raspberry Pi:**
```bash
chmod +x generate_diagrams.sh
./generate_diagrams.sh
```

This will generate PNG, SVG, and PDF versions of all diagrams.

## Output Formats

- **PNG**: Best for web viewing and presentations (default: 96 DPI)
- **SVG**: Best for documents and scaling without quality loss (recommended)
- **PDF**: Best for printing and academic papers
- **DOT**: Source files (editable)

## Customization

### Changing Output Quality

For higher resolution PNGs:
```bash
dot -Tpng -Gdpi=300 use_case_diagram.dot -o use_case_diagram_hires.png
```

### Different Layout Engines

Graphviz provides multiple layout engines:

- `dot`: Hierarchical layouts (default, used for most diagrams)
- `neato`: Spring model layouts
- `fdp`: Force-directed layouts
- `circo`: Circular layouts
- `twopi`: Radial layouts

Example using different engine:
```bash
neato -Tpng system_architecture_diagram.dot -o system_architecture_neato.png
```

## Editing Diagrams

The DOT files are plain text and can be edited with any text editor. Key syntax:

### Nodes
```dot
NodeName [label="Display Text", shape=box, style=filled, fillcolor=lightblue];
```

### Edges (Connections)
```dot
NodeA -> NodeB [label="relationship", style=bold, color=red];
```

### Clusters (Grouping)
```dot
subgraph cluster_name {
    label="Group Title";
    style=filled;
    fillcolor=lightgray;
    
    Node1;
    Node2;
}
```

## Troubleshooting

### Error: "dot: command not found"
- Graphviz is not installed or not in PATH
- Install Graphviz and ensure it's in your system PATH

### Error: "syntax error in line X"
- Check DOT file syntax
- Ensure all braces {} and brackets [] are balanced
- Verify semicolons at end of statements

### Large Diagrams Not Rendering
- Increase memory limit: `dot -Gmaxiter=10000 -Tpng file.dot -o output.png`
- Simplify diagram or split into multiple diagrams

### Overlapping Nodes
- Adjust `nodesep` and `ranksep` values in graph settings
- Try different layout engine (`neato`, `fdp`)

## Integration with Documentation

After generating diagrams, insert them into markdown documents:

```markdown
![Use Case Diagram](diagrams/use_case_diagram.png)
*Figure 3.1: Use Case Diagram showing primary actors and system interactions*
```

For LaTeX documents:
```latex
\begin{figure}[h]
  \centering
  \includegraphics[width=\textwidth]{diagrams/use_case_diagram.pdf}
  \caption{Use Case Diagram showing primary actors and system interactions}
  \label{fig:use_case}
\end{figure}
```

## References

- [Graphviz Official Documentation](https://graphviz.org/documentation/)
- [DOT Language Reference](https://graphviz.org/doc/info/lang.html)
- [Node Shapes Gallery](https://graphviz.org/doc/info/shapes.html)
- [Color Names](https://graphviz.org/doc/info/colors.html)

## License

These diagrams are part of the GyMMS academic research documentation and are subject to the same license as the main project.
