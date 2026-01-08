#!/bin/bash
# TUI Wordle Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/subinium/tui-wordle/main/install.sh | bash

set -e

REPO="subinium/tui-wordle"
INSTALL_DIR="${HOME}/.local/bin"

echo "Installing TUI Wordle..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3.11+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo "Error: Python 3.11+ is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "Found Python $PYTHON_VERSION"

# Install with pip
echo "Installing tui-wordle via pip..."
python3 -m pip install --user --upgrade tui-wordle

# Create bin directory if needed
mkdir -p "$INSTALL_DIR"

# Check if installed
if command -v wordle &> /dev/null; then
    echo ""
    echo "Installation complete!"
    echo ""
    echo "Run 'wordle' to play!"
else
    echo ""
    echo "Installation complete!"
    echo ""
    echo "You may need to add ~/.local/bin to your PATH:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo ""
    echo "Then run 'wordle' to play!"
fi
