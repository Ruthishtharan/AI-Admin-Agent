#!/bin/bash
# Replit startup script for AI IT Admin Agent
set -e

echo "========================================"
echo "  AI IT Admin Agent — Replit Startup"
echo "========================================"

echo ""
echo "[1/3] Installing Python dependencies..."
pip install -r requirements.txt -q

echo "[2/3] Installing Playwright Chromium browser..."
python3 -m playwright install chromium 2>&1 | tail -5

echo "[3/3] Starting AI IT Admin Agent..."
echo ""
python3 main.py
