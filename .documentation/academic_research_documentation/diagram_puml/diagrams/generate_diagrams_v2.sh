#!/bin/bash
# Generate all GyMMS diagrams v2 with organized output
# Usage: ./generate_diagrams_v2.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== GyMMS Diagram Generator v2 ===${NC}"
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
    "user_story_map"
)

# Create output directories
mkdir -p output/png output/svg output/pdf

# Generate diagrams
total_files=$((${#diagrams[@]} * 3))
current=0

for diagram in "${diagrams[@]}"; do
    echo -e "${YELLOW}Processing: ${diagram}${NC}"
    
    # Check if source file exists
    if [ ! -f "${diagram}.dot" ]; then
        echo -e "${RED}  ✗ Source file ${diagram}.dot not found, skipping...${NC}"
        continue
    fi
    
    # PNG (150 DPI for better quality)
    current=$((current + 1))
    output_file="output/png/${diagram}_v2.png"
    if dot -Tpng -Gdpi=150 ${diagram}.dot -o ${output_file} 2>/dev/null; then
        echo -e "${GREEN}  ✓ [${current}/${total_files}] Generated ${output_file}${NC}"
    else
        echo -e "${RED}  ✗ [${current}/${total_files}] Failed to generate ${output_file}${NC}"
    fi
    
    # SVG
    current=$((current + 1))
    output_file="output/svg/${diagram}_v2.svg"
    if dot -Tsvg ${diagram}.dot -o ${output_file} 2>/dev/null; then
        echo -e "${GREEN}  ✓ [${current}/${total_files}] Generated ${output_file}${NC}"
    else
        echo -e "${RED}  ✗ [${current}/${total_files}] Failed to generate ${output_file}${NC}"
    fi
    
    # PDF
    current=$((current + 1))
    output_file="output/pdf/${diagram}_v2.pdf"
    if dot -Tpdf ${diagram}.dot -o ${output_file} 2>/dev/null; then
        echo -e "${GREEN}  ✓ [${current}/${total_files}] Generated ${output_file}${NC}"
    else
        echo -e "${RED}  ✗ [${current}/${total_files}] Failed to generate ${output_file}${NC}"
    fi
    
    echo ""
done

echo -e "${GREEN}=== Generation Complete ===${NC}"
echo ""
echo "Output files organized by type:"
echo ""
echo -e "${CYAN}PNG files (150 DPI):${NC}"
ls -lh output/png/
echo ""
echo -e "${CYAN}SVG files:${NC}"
ls -lh output/svg/
echo ""
echo -e "${CYAN}PDF files:${NC}"
ls -lh output/pdf/

echo ""
echo "To view diagrams:"
echo "  - PNG: output/png/ directory"
echo "  - SVG: output/svg/ directory"
echo "  - PDF: output/pdf/ directory"
