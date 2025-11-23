#!/bin/bash
# Generate all GyMMS diagrams from DOT files
# Usage: ./generate_diagrams.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== GyMMS Diagram Generator ===${NC}"
echo ""

# Check if Graphviz is installed
if ! command -v dot &> /dev/null; then
    echo -e "${RED}Error: Graphviz is not installed!${NC}"
    echo "Please install Graphviz:"
    echo "  - Ubuntu/Debian: sudo apt-get install graphviz"
    echo "  - macOS: brew install graphviz"
    echo "  - Raspberry Pi: sudo apt-get install graphviz"
    exit 1
fi

echo -e "${GREEN}✓ Graphviz found: $(dot -V 2>&1)${NC}"
echo ""

# Array of diagram files (without extension)
diagrams=(
    "use_case_diagram"
    "system_architecture_diagram"
    "deployment_infrastructure_diagram"
    "database_schema_diagram"
)

# Output formats
formats=("png" "svg" "pdf")

# Create output directory if it doesn't exist
mkdir -p output

# Generate diagrams
total_files=$((${#diagrams[@]} * ${#formats[@]}))
current=0

for diagram in "${diagrams[@]}"; do
    echo -e "${YELLOW}Processing: ${diagram}${NC}"
    
    # Check if source file exists
    if [ ! -f "${diagram}.dot" ]; then
        echo -e "${RED}  ✗ Source file ${diagram}.dot not found, skipping...${NC}"
        continue
    fi
    
    for format in "${formats[@]}"; do
        current=$((current + 1))
        output_file="output/${diagram}.${format}"
        
        # Generate diagram
        if dot -T${format} ${diagram}.dot -o ${output_file} 2>/dev/null; then
            echo -e "${GREEN}  ✓ [${current}/${total_files}] Generated ${output_file}${NC}"
        else
            echo -e "${RED}  ✗ [${current}/${total_files}] Failed to generate ${output_file}${NC}"
        fi
    done
    echo ""
done

echo -e "${GREEN}=== Generation Complete ===${NC}"
echo ""
echo "Output files are in the 'output' directory:"
ls -lh output/

echo ""
echo "To view diagrams:"
echo "  - PNG: Use any image viewer"
echo "  - SVG: Open in web browser or vector graphics editor"
echo "  - PDF: Open with PDF viewer"
