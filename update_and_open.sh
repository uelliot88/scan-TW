#!/bin/bash
cd "$(dirname "$0")"

echo "================================================"
echo " Taiwan Stock Scanner"
echo "================================================"
echo ""
echo "[1/3] Updating data (takes ~10 mins)..."
echo "      Downloading ~1967 stocks in 40 batches."
echo ""

if [ ! -f "venv/bin/python" ]; then
    echo "[ERROR] venv not found. Please run setup first:"
    echo "        python3 -m venv venv"
    echo "        venv/bin/pip install -r requirements.txt"
    read -p "Press Enter to close..."
    exit 1
fi

venv/bin/python update_data.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Update failed. Check the messages above."
    read -p "Press Enter to close..."
    exit 1
fi

echo ""
echo "[2/3] Pushing to GitHub..."
git add uptrend_results.json
git commit -m "update data"
git push
if [ $? -ne 0 ]; then
    echo ""
    echo "[WARNING] GitHub push failed, but local data is updated."
fi

echo ""
echo "[3/3] Opening browser..."
open "https://scan-tw.streamlit.app/"

echo ""
echo "================================================"
echo " Done! Browser opened."
echo " Press Enter to close this window."
echo "================================================"
read -p ""
