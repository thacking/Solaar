# Haptic Cursor Feedback - GNOME Shell Extension

Provides haptic feedback when the cursor changes to a clickable/hand icon on Wayland.

## Features

- Monitors cursor shape changes in real-time using GNOME Shell's cursor tracker
- Triggers haptic feedback after cursor stays as "hand" for 150ms
- Works seamlessly on Wayland (where traditional X11 cursor monitoring isn't available)
- Integrates with Solaar's haptic D-Bus service

## Requirements

- GNOME Shell 47 or 48
- Solaar haptic daemon running (`solaar-haptic-daemon`)
- A Logitech device with haptic support

## Installation

### Option 1: Manual Installation

```bash
# Copy extension to GNOME extensions directory
mkdir -p ~/.local/share/gnome-shell/extensions/
cp -r gnome-extension/haptic-cursor-feedback@solaar ~/.local/share/gnome-shell/extensions/

# Restart GNOME Shell
# On Wayland: Log out and log back in
# On X11: Press Alt+F2, type 'r', press Enter

# Enable the extension
gnome-extensions enable haptic-cursor-feedback@solaar
```

### Option 2: Using the Install Script

```bash
cd /home/lukas/src/Hackathons/Solaar
./install-cursor-extension.sh
```

## Usage

Once installed and enabled, the extension will automatically:

1. Monitor cursor shape changes
2. Detect when cursor becomes a "hand" (clickable) icon
3. Wait 150ms to confirm the cursor stays as hand
4. Trigger haptic feedback via D-Bus call to Solaar

You should feel a haptic vibration on your supported Logitech device whenever you hover over clickable elements (links, buttons, etc.).

## Starting the Haptic Daemon

Before using this extension, make sure the Solaar haptic daemon is running:

```bash
# Start the daemon (replace with your device identifier)
bin/solaar-haptic-daemon 1  # for device in slot 1

# Or by serial/name
bin/solaar-haptic-daemon "MX Master 3S"
```

## Troubleshooting

### Check extension is enabled
```bash
gnome-extensions list --enabled | grep haptic
```

### View extension logs
```bash
journalctl -f -o cat /usr/bin/gnome-shell
```

### Test haptic service manually
```bash
gdbus call --session \
  --dest io.github.pwr_solaar.Haptics \
  --object-path /io/github/pwr_solaar/Haptics \
  --method io.github.pwr_solaar.Haptics.PlayWaveform "HAPPY ALERT"
```

### Disable extension
```bash
gnome-extensions disable haptic-cursor-feedback@solaar
```

## Supported Cursor Types

The extension triggers haptic feedback for these cursor types:
- `POINTING_HAND` - Standard hand/pointer cursor over links
- `DND_IN_DRAG` - Drag and drop cursors
- `DND_MOVE` - Move cursor
- `DND_COPY` - Copy cursor
- `DND_ASK` - Ask cursor

## Customization

To customize the delay or waveform, edit `extension.js`:

```javascript
const HAND_CURSOR_DELAY_MS = 150;  // Change delay in milliseconds
const WAVEFORM = 'HAPPY ALERT';     // Change waveform type
```

Then reload GNOME Shell for changes to take effect.

## Uninstallation

```bash
gnome-extensions disable haptic-cursor-feedback@solaar
rm -rf ~/.local/share/gnome-shell/extensions/haptic-cursor-feedback@solaar
```

## License

This extension is part of the Solaar project and follows the same license terms.
