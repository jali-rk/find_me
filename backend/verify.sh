#!/bin/bash
# Verify FindMe installation

echo "🔍 FindMe Installation Verification"
echo "===================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
echo ""

# Check directory structure
echo "Checking directory structure..."
REQUIRED_DIRS=(
    "app/core"
    "app/api/routers"
    "app/domain"
    "app/services"
    "app/utils"
    "app/templates"
    "app/static"
    "tests"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ $dir (missing)"
    fi
done
echo ""

# Check key files
echo "Checking key files..."
REQUIRED_FILES=(
    "app/main.py"
    "app/core/config.py"
    "app/services/face.py"
    "app/services/index.py"
    "requirements.txt"
    "pyproject.toml"
    ".env.example"
    "README.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
    fi
done
echo ""

# Count files
echo "File counts:"
PY_FILES=$(find . -name "*.py" -not -path "./venv/*" | wc -l)
TEST_FILES=$(find tests -name "test_*.py" 2>/dev/null | wc -l)
echo "  Python files: $PY_FILES"
echo "  Test files: $TEST_FILES"
echo ""

# Check if venv exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    
    # Check if activated
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo "✅ Virtual environment is activated"
        
        # Check key packages
        echo ""
        echo "Checking installed packages..."
        pip list | grep -E "fastapi|uvicorn|insightface|faiss-cpu|pytest" || echo "  ⚠️  Some packages may be missing"
    else
        echo "⚠️  Virtual environment not activated"
        echo "   Run: source venv/bin/activate"
    fi
else
    echo "⚠️  Virtual environment not found"
    echo "   Run: ./setup.sh"
fi

echo ""
echo "===================================="
echo "Verification complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
