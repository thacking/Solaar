# Solaar Haptic Daemon & GNOME Integration

This document explains how to keep a Logitech device "warm" for instant haptic playback and hook it into the GNOME Shell cursor so you feel a pulse whenever the pointer becomes a pointing hand over a link.

## 1. Run the daemon

```
./bin/solaar-haptic-daemon 1 --waveform "HAPPY ALERT"
```

* Replace `1` with any selector accepted by `solaar haptic` (slot number, partial name, or serial).
* Use `--hidraw /dev/hidrawX` if you want to pin the daemon to a specific receiver.
* By default the daemon exposes a DBus service `io.github.pwr_solaar.Haptics` with three methods: `PlayWaveform(string name)`, `SetLevel(string level)`, and `Ping()`.
* To keep it running across logins, create a user service `~/.config/systemd/user/solaar-haptics.service`:

```ini
[Unit]
Description=Solaar Haptic Daemon
After=graphical-session.target

[Service]
ExecStart=%h/src/Hackathons/Solaar/bin/solaar-haptic-daemon 1 --waveform "HAPPY ALERT"
Restart=on-failure

[Install]
WantedBy=default.target
```

Then run `systemctl --user enable --now solaar-haptics.service`.

## 2. Install the GNOME Shell extension

1. Copy the extension folder into your local extensions directory:
   ```
   mkdir -p ~/.local/share/gnome-shell/extensions
   cp -r gnome-shell/solaar-haptic-link@solaar ~/.local/share/gnome-shell/extensions/
   ```
2. Restart GNOME Shell (`Alt+F2`, type `r`, enter) or log out/in.
3. Enable "Solaar Haptic Link Feedback" in `gnome-extensions-app`.

The extension listens for GNOME's cursor tracker to switch to `POINTER_HAND` and immediately calls the daemon over DBus, avoiding the normal cold-start delays. Rate limiting prevents spamming the mouse when the cursor toggles quickly.

## Notes

* The cursor tracker APIs used here are private GNOME Shell internals and may change between releases. The provided metadata declares compatibility with GNOME 45–46.
* The daemon relies on Solaar's existing udev rules for hidraw access. If you still need `sudo`, ensure your user is in the `plugdev` group or adjust `/etc/udev/rules.d/42-logitech-unify-permissions.rules`.
* On Wayland the GNOME Shell extension runs inside the compositor, so it can observe cursor changes without additional privileges. On X11 you could alternatively listen for XFixes cursor notifications and call the DBus service manually.
