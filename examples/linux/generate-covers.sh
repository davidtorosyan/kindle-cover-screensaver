#!/bin/sh
# Example: regenerate Kindle covers from a Calibre library on Linux/macOS.
#
# Copy this file to generate-covers.local.sh (git-ignored) and fill in the paths.

LIBRARY="$HOME/Calibre Library"
OUTPUT="/srv/kindle/covers"

kindle-covers generate "$LIBRARY" "$OUTPUT" \
    --device kindle_paperwhite2 \
    --filter-column "Read" --filter-value "True" \
    --border-color black \
    --clean
