param(
    [string]$TargetDirectory = ""
)

# Script to convert all .h264 files to .mp4 files using ffmpeg
# Usage: .\convert_h264_to_mp4.ps1 [target_directory]
# If no directory is provided, it will prompt for one

# Check if ffmpeg is installed
try {
    $null = Get-Command ffmpeg -ErrorAction Stop
}
catch {
    Write-Host "Error: ffmpeg is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install ffmpeg before running this script" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Get target directory from parameter or prompt user
if ([string]::IsNullOrEmpty($TargetDirectory)) {
    $TargetDirectory = Read-Host "Enter the path to the directory containing .h264 files"
}

# Validate target directory
if (-not (Test-Path -Path $TargetDirectory -PathType Container)) {
    Write-Host "Error: Directory '$TargetDirectory' does not exist" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Convert to absolute path and change to target directory
$TargetDirectory = Resolve-Path $TargetDirectory
Write-Host "Target directory: $TargetDirectory" -ForegroundColor Green
Write-Host "Changing to target directory..." -ForegroundColor Yellow
Set-Location $TargetDirectory

# Function to convert a single h264 file to mp4
function Convert-H264ToMp4 {
    param(
        [string]$InputFile
    )
    
    $OutputFile = [System.IO.Path]::ChangeExtension($InputFile, ".mp4")
    $InputFileName = [System.IO.Path]::GetFileName($InputFile)
    $OutputFileName = [System.IO.Path]::GetFileName($OutputFile)
    
    Write-Host "Converting: $InputFileName -> $OutputFileName" -ForegroundColor Cyan
    
    # Use ffmpeg to convert h264 to mp4
    $process = Start-Process -FilePath "ffmpeg" -ArgumentList "-i", "`"$InputFile`"", "-c", "copy", "-f", "mp4", "`"$OutputFile`"", "-y" -NoNewWindow -Wait -PassThru
    
    if ($process.ExitCode -eq 0) {
        Write-Host "Successfully converted: $OutputFileName" -ForegroundColor Green
        return $true
    } else {
        Write-Host "Failed to convert: $InputFileName" -ForegroundColor Red
        return $false
    }
}

# Initialize counters
$convertedFiles = 0
$failedFiles = 0

# Find all .h264 files
Write-Host "Scanning for .h264 files..." -ForegroundColor Yellow
$h264Files = Get-ChildItem -Path . -Filter "*.h264" -Recurse -File

$totalFiles = $h264Files.Count
Write-Host "Found $totalFiles .h264 files to convert" -ForegroundColor Green
Write-Host "Starting conversion..." -ForegroundColor Yellow
Write-Host "----------------------------------------"

# Process each file
foreach ($file in $h264Files) {
    # Check if corresponding .mp4 file already exists
    $mp4File = [System.IO.Path]::ChangeExtension($file.FullName, ".mp4")
    
    if (Test-Path $mp4File) {
        Write-Host "Skipping $($file.Name) (MP4 already exists)" -ForegroundColor Yellow
        $convertedFiles++
        continue
    }
    
    # Convert the file
    if (Convert-H264ToMp4 -InputFile $file.FullName) {
        $convertedFiles++
    } else {
        $failedFiles++
    }
    
    $progress = $convertedFiles + $failedFiles
    Write-Host "Progress: $progress/$totalFiles" -ForegroundColor Magenta
    Write-Host "----------------------------------------"
}

# Summary
Write-Host ""
Write-Host "Conversion Summary:" -ForegroundColor Green
Write-Host "=================="
Write-Host "Total files found: $totalFiles"
Write-Host "Successfully converted: $convertedFiles" -ForegroundColor Green
Write-Host "Failed conversions: $failedFiles" -ForegroundColor Red

if ($failedFiles -eq 0) {
    Write-Host "All conversions completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Some conversions failed. Check the output above for details." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"