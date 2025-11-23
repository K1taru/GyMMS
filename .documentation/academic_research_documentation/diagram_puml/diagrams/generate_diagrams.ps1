# PowerShell script to generate all GyMMS diagrams from DOT files
# Usage: .\generate_diagrams.ps1

Write-Host "=== GyMMS Diagram Generator ===" -ForegroundColor Yellow
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
    "database_schema_diagram"
)

# Output formats
$formats = @("png", "svg", "pdf")

# Create output directory if it doesn't exist
$outputDir = "output"
if (-not (Test-Path $outputDir))
{
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# Generate diagrams
$totalFiles = $diagrams.Count * $formats.Count
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
    
    foreach ($format in $formats)
    {
        $current++
        $outputFile = "$outputDir\$diagram.$format"
        
        # Generate diagram
        $result = & dot "-T$format" $sourceFile -o $outputFile 2>&1
        if ($LASTEXITCODE -eq 0)
        {
            Write-Host "  ✓ [$current/$totalFiles] Generated $outputFile" -ForegroundColor Green
        }
        else
        {
            Write-Host "  ✗ [$current/$totalFiles] Failed to generate $outputFile" -ForegroundColor Red
        }
    }
    Write-Host ""
}

Write-Host "=== Generation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Output files are in the 'output' directory:"
Get-ChildItem -Path $outputDir | Format-Table Name, Length, LastWriteTime

Write-Host ""
Write-Host "To view diagrams:"
Write-Host "  - PNG: Use any image viewer (Photos, Paint, etc.)"
Write-Host "  - SVG: Open in web browser or vector graphics editor"
Write-Host "  - PDF: Open with PDF viewer (Edge, Adobe Reader, etc.)"
