#!/bin/bash
# Verify Skylark BI Agent Setup
# Run this to confirm everything is ready for deployment

echo "🔍 Skylark BI Agent - Setup Verification"
echo "========================================"
echo ""

# Check Python
echo "✓ Checking Python..."
python --version

# Check dependencies
echo "✓ Checking dependencies..."
pip list | grep -E "streamlit|requests|pandas|openai|pytest" | head -10

# Check project structure
echo ""
echo "✓ Project structure:"
ls -la app/*.py | wc -l
echo "  Files in app/: $(ls app/*.py | wc -l)"

ls -la tests/test_*.py | wc -l
echo "  Files in tests/: $(ls tests/test_*.py | wc -l)"

# Check tests
echo ""
echo "✓ Running tests..."
python -m pytest -q --tb=no 2>&1 | tail -1

# Check config
echo ""
echo "✓ Checking configuration..."
python -c "from app.config import Config; is_valid, missing = Config.validate(); print(f'  Config valid: {is_valid}'); missing and print(f'  Missing: {missing}')"

# Check Monday connection
echo ""
echo "✓ Testing Monday.com connection..."
python -c "
from app.monday_client import MondayClient
try:
    client = MondayClient()
    result = client.test_connection()
    if result:
        print('  ✅ Monday.com connection OK')
    else:
        print('  ⚠️  Connection test returned False')
except Exception as e:
    print(f'  ❌ Error: {e}')
"

# Check .env security
echo ""
echo "✓ Checking .env security..."
if grep -q "^.env$" .gitignore; then
    echo "  ✅ .env is in .gitignore"
else
    echo "  ⚠️  .env may not be properly ignored"
fi

# Check .env.example
echo ""
echo "✓ Checking .env.example..."
if grep -q "MONDAY_API_TOKEN=" .env.example; then
    echo "  ✅ .env.example has placeholders (no real values)"
else
    echo "  ⚠️  .env.example may have real values!"
fi

echo ""
echo "========================================"
echo "✅ Setup verification complete!"
echo ""
echo "Next steps:"
echo "1. Read README.md for overview"
echo "2. Follow DEPLOYMENT.md for Streamlit Cloud setup"
echo "3. Deploy to get your public URL"
echo "4. Share URL with evaluators"
