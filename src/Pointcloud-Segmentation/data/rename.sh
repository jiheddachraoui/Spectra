#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$(dirname "$0")"

# Change directory to the script's directory
cd "$SCRIPT_DIR" || exit

# Counter variable to track the number in the file names
counter=0

# Loop through all the files in the directory sorted by name
for file in $(ls -1v *.{jpg,jpeg,png,gif,bmp,pcd,h5,bin,label}); do
    # Pad the counter to two digits with leading zeros
    new_name=$(printf "%06d" "$counter")

    # Get the file extension
    ext="${file##*.}"

    # Rename the file
    mv -- "$file" "${new_name}.${ext}"

    # Increment the counter
    ((counter++))
done

echo "Renaming complete."

