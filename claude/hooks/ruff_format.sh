#!/bin/bash

# Claude Code hook script to format Python files with ruff
# This script receives file paths as arguments and formats only .py files

# Set strict error handling
set -euo pipefail

# Configuration
LOGFILE="${CLAUDE_LOGFILE:-/tmp/claude-format.log}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Logging function
log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOGFILE"
}

# Check if ruff is available
if ! command -v ruff &> /dev/null; then
    log "ERROR: ruff is not installed or not in PATH"
    exit 1
fi

# If no arguments provided, exit gracefully
if [[ $# -eq 0 ]]; then
    log "INFO: No files provided to format"
    exit 0
fi

log "INFO: Starting Python file formatting for $# file(s)"

formatted_count=0
error_count=0

# Process each file argument
for file in "$@"; do
    # Skip if not a Python file
    if [[ "$file" != *.py ]]; then
        continue
    fi
    
    # Check if file exists
    if [[ ! -f "$file" ]]; then
        log "WARNING: File does not exist: $file"
        continue
    fi
    
    # Format the file
    log "INFO: Formatting $file"
    if ruff format "$file" 2>/dev/null; then
        log "SUCCESS: Formatted $file"
        ((formatted_count++))
    else
        log "ERROR: Failed to format $file"
        ((error_count++))
    fi
done

log "INFO: Formatting complete. Formatted: $formatted_count, Errors: $error_count"

# Exit with error if any files failed to format
if [[ $error_count -gt 0 ]]; then
    exit 1
fi
