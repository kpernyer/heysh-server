#!/bin/bash

# UV Setup Script
# This script sets up the development environment using uv instead of pip

set -e

echo "🚀 Setting up development environment with uv"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    echo "✅ uv installed"
else
    echo "✅ uv already installed"
fi

# Check uv version
echo "🔍 uv version: $(uv --version)"

# Setup backend with uv
echo "🐍 Setting up Python backend with uv..."
cd backend

# Create virtual environment with uv
echo "📦 Creating virtual environment..."
uv venv

# Install dependencies
echo "📦 Installing dependencies..."
uv pip install --upgrade pip setuptools wheel
uv pip install -e '.[dev]'

# Install additional development tools
echo "📦 Installing development tools..."
uv add --dev pytest pytest-asyncio pytest-cov pytest-mock
uv add --dev black ruff mypy bandit pre-commit
uv add --dev httpx factory-boy faker freezegun
uv add --dev pytest-xdist pytest-benchmark pytest-html pytest-json-report
uv add --dev coverage tox safety pip-audit
uv add --dev mypy-extensions types-requests types-redis types-PyYAML types-jsonschema

echo "✅ Backend setup completed with uv"

# Setup frontend
echo "📦 Setting up Node.js frontend..."
cd ..

if command -v pnpm &> /dev/null; then
    echo "📦 Installing with pnpm..."
    pnpm install
else
    echo "📦 Installing with npm..."
    npm install
fi

echo "✅ Frontend setup completed"

# Setup pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
cd backend
uv run pre-commit install
cd ..

echo "✅ Pre-commit hooks installed"

# Verify installation
echo "🧪 Verifying installation..."

# Test Python environment
echo "🐍 Testing Python environment..."
cd backend
if uv run python -c "import fastapi, uvicorn, pydantic, structlog; print('✅ Core dependencies working')"; then
    echo "✅ Python environment verified"
else
    echo "❌ Python environment verification failed"
    exit 1
fi

# Test development tools
echo "🔧 Testing development tools..."
if uv run black --version && uv run ruff --version && uv run mypy --version; then
    echo "✅ Development tools verified"
else
    echo "❌ Development tools verification failed"
    exit 1
fi

cd ..

# Test Node environment
echo "📦 Testing Node environment..."
if node --version && npm --version; then
    echo "✅ Node environment verified"
else
    echo "❌ Node environment verification failed"
    exit 1
fi

echo ""
echo "🎉 UV Setup Complete!"
echo ""
echo "✅ Python backend setup with uv"
echo "✅ Node.js frontend setup"
echo "✅ Pre-commit hooks installed"
echo "✅ Development tools verified"
echo ""
echo "Available commands:"
echo "  - uv run python <script>     # Run Python scripts"
echo "  - uv run pytest              # Run tests"
echo "  - uv run black .             # Format code"
echo "  - uv run ruff check .        # Lint code"
echo "  - uv run mypy .              # Type check"
echo "  - uv run bandit .            # Security scan"
echo ""
echo "Development workflow:"
echo "  1. just setup                 # Setup both frontend and backend"
echo "  2. just dev                   # Start frontend"
echo "  3. just dev-api               # Start backend"
echo "  4. just test                  # Run tests"
echo "  5. just lint                  # Lint code"
echo ""
echo "For more information, see: doc/DEVELOPMENT.md"
