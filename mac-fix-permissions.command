#!/bin/bash
# Premier Cost Engine — macOS unblock script
# Double-click this file ONCE after installing to allow the app to run

APP="/Applications/Premier Cost Engine.app"

if [ ! -d "$APP" ]; then
    echo "ERROR: Premier Cost Engine not found at $APP"
    echo "Please install the app first by dragging it to Applications."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

echo "Removing macOS quarantine flag from Premier Cost Engine..."
xattr -cr "$APP" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Done! You can now open Premier Cost Engine normally."
    echo ""
    echo "If macOS still blocks it, go to:"
    echo "  System Settings → Privacy & Security → click 'Open Anyway'"
else
    echo "ERROR: Could not modify app permissions."
    echo "Try running: sudo xattr -cr \"$APP\""
fi

echo ""
read -p "Press Enter to close..."
