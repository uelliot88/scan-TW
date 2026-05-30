#!/usr/bin/env bash
cd "$(dirname "$0")"

echo "================================================"
echo " Taiwan Stock Scanner"
echo "================================================"
echo ""

VENV_PYTHON="venv/bin/python"
VENV_PIP="venv/bin/pip"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] venv not found. Please run setup first:"
    echo "        python3 -m venv venv"
    echo "        $VENV_PIP install -r requirements.txt"
    read -p "Press Enter to close..."
    exit 1
fi

echo "[1/4] Updating market themes..."
if [ -f "update_stock_concepts.py" ]; then
    "$VENV_PYTHON" update_stock_concepts.py
    if [ $? -ne 0 ]; then
        echo ""
        echo "[WARNING] Market theme update failed. Continuing with existing local market theme data."
    fi
else
    echo "      Local-only updater not found. Reusing existing stock_concepts.json."
fi

echo ""
echo "[2/4] Updating data (takes ~10 mins)..."
echo "      Downloading ~1968 stocks in 40 batches."
echo ""

"$VENV_PYTHON" update_data.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Update failed. Check the messages above."
    read -p "Press Enter to close..."
    exit 1
fi

echo ""
echo "[3/4] Pushing to GitHub..."
git add uptrend_results.json stock_concepts.json
if git diff --cached --quiet; then
    echo "      No data changes to commit."
else
    git commit -m "update data"
    if [ $? -ne 0 ]; then
        echo ""
        echo "[WARNING] Git commit failed, but local data is updated."
    else
        git push
        if [ $? -ne 0 ]; then
            echo ""
            echo "[WARNING] GitHub push failed, but local data is updated."
        fi
    fi
fi

echo ""
echo "[4/4] Opening browser..."
if command -v open >/dev/null 2>&1; then
    open "https://scan-tw.streamlit.app/"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "https://scan-tw.streamlit.app/" >/dev/null 2>&1 &
else
    echo "      Open this URL manually: https://scan-tw.streamlit.app/"
fi

echo ""
echo "================================================"
echo " Done! Browser opened."
echo " Press Enter to close this window."
echo "================================================"
read -p ""
