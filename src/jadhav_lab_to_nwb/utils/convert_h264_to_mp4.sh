#!/bin/bash

# Script to convert all .h264 files to .mp4 files using ffmpeg
# Usage: ./convert_h264_to_mp4.sh [target_directory]
# If no directory is provided, it will prompt for one

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed or not in PATH"
    echo "Please install ffmpeg before running this script"
    exit 1
fi

# Get target directory from command line argument or prompt user
if [ $# -eq 1 ]; then
    TARGET_DIR="$1"
elif [ $# -eq 0 ]; then
    echo "Enter the path to the directory containing .h264 files:"
    read -r TARGET_DIR
else
    echo "Usage: $0 [target_directory]"
    echo "Example: $0 /Volumes/T7/CatalystNeuro/Jadhav/CoopLearnProject/CohortAS1/Social\ W/100%/XFN1-XFN3"
    exit 1
fi

# Validate target directory
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist"
    exit 1
fi

# Convert to absolute path and change to target directory
TARGET_DIR=$(realpath "$TARGET_DIR")
echo "Target directory: $TARGET_DIR"
echo "Changing to target directory..."
cd "$TARGET_DIR" || {
    echo "Error: Cannot access directory '$TARGET_DIR'"
    exit 1
}

# Function to convert a single h264 file to mp4
convert_file() {
    local input_file="$1"
    local output_file="${input_file%.h264}.mp4"

    echo "Converting: $input_file -> $output_file"

    # Use ffmpeg to convert h264 to mp4
    ffmpeg -i "$input_file" -c copy -f mp4 "$output_file" -y 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "✓ Successfully converted: $(basename "$output_file")"
        return 0
    else
        echo "✗ Failed to convert: $input_file"
        return 1
    fi
}

# Counter for tracking progress
converted_files=0
failed_files=0

# Collect all .h264 files into an array (compatible with older bash)
echo "Scanning for .h264 files..."
h264_files=()
while IFS= read -r -d '' file; do
    h264_files+=("$file")
done < <(find . -name "*.h264" -type f -print0)

total_files=${#h264_files[@]}
echo "Found $total_files .h264 files to convert"
echo "Starting conversion..."
echo "----------------------------------------"

# Process each file
for file in "${h264_files[@]}"; do
    # Check if corresponding .mp4 file already exists
    mp4_file="${file%.h264}.mp4"
    if [ -f "$mp4_file" ]; then
        echo "⚠ Skipping $file (MP4 already exists)"
        ((converted_files++))
        continue
    fi

    # Convert the file
    if convert_file "$file"; then
        ((converted_files++))
    else
        ((failed_files++))
    fi

    echo "Progress: $((converted_files + failed_files))/$total_files"
    echo "----------------------------------------"
done

# Summary
echo ""
echo "Conversion Summary:"
echo "=================="
echo "Total files found: $total_files"
echo "Successfully converted: $converted_files"
echo "Failed conversions: $failed_files"

if [ $failed_files -eq 0 ]; then
    echo "🎉 All conversions completed successfully!"
else
    echo "⚠ Some conversions failed. Check the output above for details."
fi
