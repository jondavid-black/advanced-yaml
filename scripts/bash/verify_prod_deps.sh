#!/bin/bash
set -e

# Description: Verifies that the package runs with ONLY production dependencies.
# Usage: ./scripts/bash/verify_prod_deps.sh

# Create a temporary directory for the test
TEMP_DIR=$(mktemp -d)
echo "Testing in temporary directory: $TEMP_DIR"

# Ensure cleanup happens
cleanup() {
    rm -rf "$TEMP_DIR"
    echo "Cleaned up."
}
trap cleanup EXIT

# Create a virtual environment using uv
echo "Creating isolated virtual environment..."
uv venv "$TEMP_DIR/.venv"

# Install the package dependencies ONLY (no dev extras)
# We use 'uv pip install' pointing to the current directory
echo "Installing production dependencies..."
uv pip install -p "$TEMP_DIR/.venv/bin/python" .

# Verification 1: Ensure dev tools are NOT present
echo "Verifying environment isolation..."
if "$TEMP_DIR/.venv/bin/python" -c "import pytest" 2>/dev/null; then
    echo "❌ Test Failed: 'pytest' (dev dependency) was found in the environment."
    exit 1
else
    echo "✅ isolation check passed (pytest not found)"
fi

# Verification 2: Run the help commands for each CLI tool
# This catches missing runtime dependencies (ImportErrors)
echo "Verifying CLI entry points..."
TOOLS=("yasl" "yaql" "yarl" "yatl")
FAILED=0

for tool in "${TOOLS[@]}"; do
    echo -n "Checking $tool... "
    if "$TEMP_DIR/.venv/bin/$tool" --help > /dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "❌ FAILED"
        echo "Output from $tool:"
        "$TEMP_DIR/.venv/bin/$tool" --help || true
        FAILED=1
    fi
done

if [ $FAILED -eq 1 ]; then
    echo "💥 verification failed. Some tools could not run."
    exit 1
fi

echo "🎉 All tools run successfully with strictly production dependencies!"
