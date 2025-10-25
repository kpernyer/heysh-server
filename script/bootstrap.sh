#!/bin/bash
# Bootstrap script for hey-sh backend

set -e

echo "🚀 Bootstrapping hey-sh backend..."
echo ""

# Check for required tools
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker"
    exit 1
fi
echo "✅ Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose not found. Trying docker compose..."
    if ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose not found. Please install Docker Compose"
        exit 1
    fi
fi
echo "✅ Docker Compose"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo ""
    echo "📦 Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo "✅ uv $(uv --version | cut -d' ' -f2)"

# Install just if not present
if ! command -v just &> /dev/null; then
    echo ""
    echo "📦 Installing just (command runner)..."
    if command -v cargo &> /dev/null; then
        cargo install just
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install just
        else
            echo "⚠️  Please install just manually: https://github.com/casey/just"
        fi
    else
        echo "⚠️  Please install just manually: https://github.com/casey/just"
    fi
fi

if command -v just &> /dev/null; then
    echo "✅ just $(just --version | cut -d' ' -f2)"
else
    echo "⚠️  just not installed, you can still use python/docker directly"
fi

echo ""
echo "🔧 Setting up environment..."

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

echo ""
echo "✅ Bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Run: just bootstrap (or: uv pip install -e .[dev])"
echo "  3. Run: just dev (or: docker-compose -f docker/docker-compose.yml up)"
echo "  4. Visit http://localhost:8080 (Temporal UI)"
echo ""
