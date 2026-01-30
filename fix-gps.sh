#!/bin/bash

# GPS Auto-Detection Fix
# This script helps you access the site via localhost so GPS works

echo "🔧 GPS Auto-Detection Fix"
echo "=========================="
echo ""
echo "GPS is blocked on http://192.168.1.21:8000 due to browser security."
echo "To enable GPS auto-detection, use one of these methods:"
echo ""
echo "📍 Method 1: Use Localhost (EASIEST)"
echo "   Instead of: http://192.168.1.21:8000"
echo "   Use:        http://127.0.0.1:8000"
echo ""
echo "   ✅ GPS will work on localhost!"
echo ""
echo "📍 Method 2: Install ngrok for HTTPS"
echo "   1. Install: brew install ngrok"
echo "   2. Run: ngrok http 8000"
echo "   3. Use the https://xxx.ngrok.io URL"
echo ""
echo "   ✅ GPS will work on HTTPS!"
echo ""
echo "🎯 Quick Test:"
echo "   Open: http://127.0.0.1:8000/report-waste/"
echo "   GPS should work automatically!"
echo ""
