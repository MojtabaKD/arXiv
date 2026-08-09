#!/bin/bash
# organize_pdfs_dryrun.sh
# Move PDFs into MediaWiki?style hash subdirectories:
#   e.g., hash "abcdef" ? ./a/ab/ (first char, then first two chars)
# Keeps original filenames.

# ===== CONFIGURATION =====
HASH_CMD="md5sum"
DRY_RUN=true          # Set to false for real execution
TARGET_DIR="${1:-.}"  # Use first argument or current dir
# =========================

# Check hash command
if ! command -v "$HASH_CMD" &> /dev/null; then
    echo "Error: $HASH_CMD not found. Install it or change HASH_CMD."
    exit 1
fi

echo "?? Target directory: $TARGET_DIR"
if [ "$DRY_RUN" = true ]; then
    echo "?? DRY RUN mode ? no files will be moved."
else
    echo "?? LIVE mode ? files WILL be moved."
fi
echo "------------------------"

# Find all PDFs recursively
find "$TARGET_DIR" -type f -iname "*.pdf" -print0 | while IFS= read -r -d '' file; do
    # Compute hash (e.g., md5sum)
    hash=$($HASH_CMD "$file" | awk '{print $1}')
    if [ -z "$hash" ]; then
        echo "? Failed to compute hash for $file" >&2
        continue
    fi

    # Build MediaWiki?style nested path:
    #   first character, then first two characters
    first_char="${hash:0:1}"
    first_two="${hash:0:2}"
    # In case hash is shorter than expected (should not happen), use fallback
    [ -z "$first_char" ] && first_char="_"
    [ -z "$first_two" ] && first_two="__"

    dest_dir="${TARGET_DIR}/$first_char/$first_two"
    original_name="$(basename "$file")"
    dest_file="$dest_dir/$original_name"

    # ---- DRY RUN ----
    if [ "$DRY_RUN" = true ]; then
        if [ -e "$dest_file" ]; then
            echo "??  [DRY] Would skip (conflict): $file"
            echo "        ? Destination already exists: $dest_file"
        else
            echo "?? [DRY] Would move: $file"
            echo "        ? To: $dest_file"
        fi
        continue
    fi

    # ---- LIVE ----
    mkdir -p "$dest_dir" || { echo "? Failed to create $dest_dir" >&2; continue; }

    if [ -e "$dest_file" ]; then
        echo "??  Conflict: $file would overwrite $dest_file. Skipping."
        # Uncomment to delete the source file: rm "$file"
        continue
    fi

    mv "$file" "$dest_file"
    echo "? Moved $file -> $dest_file"
done

echo "------------------------"
if [ "$DRY_RUN" = true ]; then
    echo "?? DRY RUN complete. No files were changed."
    echo "   Set DRY_RUN=false in the script and run again to actually move."
fi