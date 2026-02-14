#!/bin/bash
# Entrypoint script for Discord Bot
# Compatible with both Docker and WispByte hosting environments

set -e  # Exit on error

echo "========================================"
echo "  Discord Bot - Starting..."
echo "========================================"
echo ""

# Determine the script directory and bot directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📂 Script directory: $SCRIPT_DIR"

# Change to the bot directory
# This handles both standard Docker (/app) and WispByte (/home/container) setups
cd "$SCRIPT_DIR" || {
    echo "❌ Error: Cannot change to script directory"
    exit 1
}
echo "📂 Working directory: $(pwd)"
echo ""

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "🔧 Loading environment variables from .env..."
    # Export variables from .env file safely
    # Filter out comments and empty lines, only keep valid variable assignments
    while IFS='=' read -r key value; do
        # Skip if key is empty or starts with #
        [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
        # Export the variable
        export "$key=$value"
    done < <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' .env)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: .env file not found, using environment variables only"
fi
echo ""

# Verify required environment variables
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "❌ Error: DISCORD_BOT_TOKEN is not set!"
    echo "Please set DISCORD_BOT_TOKEN in your .env file or environment variables"
    exit 1
fi
echo "✅ DISCORD_BOT_TOKEN is set"
echo ""

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p data/backups
mkdir -p logs
echo "✅ Directories created:"
echo "   - data/"
echo "   - data/backups/"
echo "   - logs/"
echo ""

# Check if bot.py exists
if [ ! -f bot.py ]; then
    echo "❌ Error: bot.py not found in $(pwd)"
    echo "Directory contents:"
    ls -la
    exit 1
fi
echo "✅ bot.py found"
echo ""

# Check Python version
echo "🐍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "   $PYTHON_VERSION"
echo ""

# Start the bot
echo "🚀 Starting Discord Bot..."
echo "========================================"
echo ""

# Run the bot with unbuffered output
exec python3 -u bot.py
