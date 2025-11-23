# PowerShell script to generate all GyMMS diagrams v2 with organized output
# Usage: .\generate_diagrams_v2.ps1

Write-Host "=== GyMMS Diagram Generator v2 ===" -ForegroundColor Yellow
Write-Host ""

# Check if Graphviz is installed
$dotCommand = Get-Command dot -ErrorAction SilentlyContinue
if (-not $dotCommand)
{
    Write-Host "Error: Graphviz is not installed!" -ForegroundColor Red
    Write-Host "Please install Graphviz:"
    Write-Host "  - Using Chocolatey: choco install graphviz"
    Write-Host "  - Or download from: https://graphviz.org/download/"
    Write-Host ""
    Write-Host "After installation, restart PowerShell and try again."
    exit 1
}

$version = & dot -V 2>&1
Write-Host "✓ Graphviz found: $version" -ForegroundColor Green
Write-Host ""

# Array of diagram files (without extension)
$diagrams = @(
    "use_case_diagram",
    "system_architecture_diagram",
    "deployment_infrastructure_diagram",
    "database_schema_diagram",
    "user_story_map"
)

# Create output directories
$outputDirs = @("output/png", "output/svg", "output/pdf")
foreach ($dir in $outputDirs)
{
    if (-not (Test-Path $dir))
    {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Generate diagrams
$totalFiles = $diagrams.Count * 3
$current = 0

foreach ($diagram in $diagrams)
{
    Write-Host "Processing: $diagram" -ForegroundColor Yellow
    
    $sourceFile = "$diagram.dot"
    
    # Check if source file exists
    if (-not (Test-Path $sourceFile))
    {
        Write-Host "  ✗ Source file $sourceFile not found, skipping..." -ForegroundColor Red
        continue
    }
    
    # PNG
    $current++
    $outputFile = "output/png/${diagram}_v2.png"
    $result = & dot -Tpng -Gdpi=150 $sourceFile -o $outputFile 2>&1
    if ($LASTEXITCODE -eq 0)
    {
        Write-Host "  ✓ [$current/$totalFiles] Generated $outputFile" -ForegroundColor Green
    }
    else
    {
        Write-Host "  ✗ [$current/$totalFiles] Failed to generate $outputFile" -ForegroundColor Red
    }
    
    # SVG
    $current++
    $outputFile = "output/svg/${diagram}_v2.svg"
    $result = & dot -Tsvg $sourceFile -o $outputFile 2>&1
    if ($LASTEXITCODE -eq 0)
    {
        Write-Host "  ✓ [$current/$totalFiles] Generated $outputFile" -ForegroundColor Green
    }
    else
    {
        Write-Host "  ✗ [$current/$totalFiles] Failed to generate $outputFile" -ForegroundColor Red
    }
    
    # PDF
    $current++
    $outputFile = "output/pdf/${diagram}_v2.pdf"
    $result = & dot -Tpdf $sourceFile -o $outputFile 2>&1
    if ($LASTEXITCODE -eq 0)
    {
        Write-Host "  ✓ [$current/$totalFiles] Generated $outputFile" -ForegroundColor Green
    }
    else
    {
        Write-Host "  ✗ [$current/$totalFiles] Failed to generate $outputFile" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "=== Generation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Output files organized by type:"
Write-Host ""
Write-Host "PNG files (150 DPI):" -ForegroundColor Cyan
Get-ChildItem -Path "output/png" | Format-Table Name, Length, LastWriteTime
Write-Host "SVG files:" -ForegroundColor Cyan
Get-ChildItem -Path "output/svg" | Format-Table Name, Length, LastWriteTime
Write-Host "PDF files:" -ForegroundColor Cyan
Get-ChildItem -Path "output/pdf" | Format-Table Name, Length, LastWriteTime

Write-Host ""
Write-Host "To view diagrams:"
Write-Host "  - PNG: output/png/ directory"
Write-Host "  - SVG: output/svg/ directory"
Write-Host "  - PDF: output/pdf/ directory"
