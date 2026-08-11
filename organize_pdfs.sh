#!/bin/bash

HASH_CMD="md5sum"
DRY_RUN=true
TARGET_DIR="${1:-.}"

if ! command -v "$HASH_CMD" &> /dev/null; then
    echo "Error: $HASH_CMD not found."
    exit 1
fi

echo "Target directory: $TARGET_DIR"
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN mode - no files will be moved."
else
    echo "LIVE mode - files WILL be moved."
fi
echo "------------------------"

find "$TARGET_DIR" -type f -iname "*.pdf" -print0 | while IFS= read -r -d '' file; do
    hash=$($HASH_CMD "$file" | awk '{print $1}')
    if [ -z "$hash" ]; then
        echo "Failed to compute hash for $file" >&2
        continue
    fi

    first_char="${hash:0:1}"
    first_two="${hash:0:2}"
    first_three="${hash:0:3}"
    [ -z "$first_char" ] && first_char="_"
    [ -z "$first_two" ] && first_two="__"
    [ -z "$first_three" ] && first_three="___"

    dest_dir="${TARGET_DIR}/$first_char/$first_two/$first_three"
    original_name="$(basename "$file")"
    dest_file="$dest_dir/$original_name"

    if [ "$DRY_RUN" = true ]; then
        if [ -e "$dest_file" ]; then
            echo "[DRY] Would skip (conflict): $file"
            echo "      Destination already exists: $dest_file"
        else
            echo "[DRY] Would move: $file"
            echo "      To: $dest_file"
        fi
        continue
    fi

    mkdir -p "$dest_dir" || { echo "Failed to create $dest_dir" >&2; continue; }

    if [ -e "$dest_file" ]; then
        echo "Conflict: $file would overwrite $dest_file. Skipping."
        continue
    fi

    mv "$file" "$dest_file"
    echo "Moved $file -> $dest_file"
done

echo "------------------------"
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN complete. No files were changed."
    echo "Set DRY_RUN=false in the script and run again to actually move."
fi