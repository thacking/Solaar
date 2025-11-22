#!/usr/bin/env bash
# Install script for Haptic Cursor Feedback GNOME Shell Extension

set -e

EXTENSION_UUID="haptic-cursor-feedback@solaar"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gnome-extension/$EXTENSION_UUID"

echo "Installing Haptic Cursor Feedback Extension..."

# Create extensions directory if it doesn't exist
mkdir -p "$HOME/.local/share/gnome-shell/extensions"

# Copy extension files
echo "Copying extension files to $EXTENSION_DIR..."
cp -r "$SOURCE_DIR" "$EXTENSION_DIR"

echo ""
echo "✓ Extension installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Restart GNOME Shell:"
echo "     - On Wayland: Log out and log back in"
echo "     - On X11: Press Alt+F2, type 'r', and press Enter"
echo ""
echo "  2. Enable the extension:"
echo "     gnome-extensions enable $EXTENSION_UUID"
echo ""
echo "  3. Start the haptic daemon (if not already running):"
echo "     bin/solaar-haptic-daemon <device>"
echo ""
echo "  4. Test the extension by hovering over clickable elements (links, buttons)"
echo ""
