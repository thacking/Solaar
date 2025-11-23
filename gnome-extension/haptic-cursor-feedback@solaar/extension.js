// extension.js - Haptic Cursor Feedback Extension for GNOME Shell 47/48
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Meta from 'gi://Meta';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const HAND_CURSOR_DELAY_MS = 0;
const CURSOR_CHECK_INTERVAL_MS = 5; // Check cursor every 50ms
const DBUS_NAME = 'io.github.pwr_solaar.Haptics';
const DBUS_PATH = '/io/github/pwr_solaar/Haptics';
const DBUS_INTERFACE = 'io.github.pwr_solaar.Haptics';
const DEFAULT_WAVEFORM = 'DAMP COLLISION';
const SETTINGS_FILE_PATH = GLib.build_filenamev([GLib.get_home_dir(), '.config', 'haptics', 'settings.json']);

export default class HapticCursorExtension {
    constructor() {
        this._cursorTracker = null;
        this._cursorChangedId = null;
        this._pollTimeoutId = null;
        this._handCursorTimeoutId = null;
        this._lastSprite = null;
        this._isHandCursor = false;
        this._hapticTriggered = false;
        this._handCursorStartTime = null;
        this._waveform = DEFAULT_WAVEFORM;
        this._settingsFileMonitor = null;
        this._settingsMonitorId = null;
    }

    enable() {
        log('[HapticCursor] Enabling extension');
        
        // Load settings from file
        this._loadSettings();
        
        // Monitor settings file for changes
        this._setupSettingsMonitor();
        
        // Get the cursor tracker from the compositor backend
        this._cursorTracker = global.backend.get_cursor_tracker();
        
        // Connect to cursor-changed signal to wake up polling
        this._cursorChangedId = this._cursorTracker.connect(
            'cursor-changed',
            this._onCursorChanged.bind(this)
        );
        
        // Start periodic cursor checking
        this._startPolling();
        
        log('[HapticCursor] Extension enabled, monitoring cursor changes');
    }

    disable() {
        log('[HapticCursor] Disabling extension');
        
        // Stop polling
        this._stopPolling();
        
        // Stop monitoring settings file
        this._cleanupSettingsMonitor();
        
        // Disconnect cursor tracker signal
        if (this._cursorChangedId && this._cursorTracker) {
            this._cursorTracker.disconnect(this._cursorChangedId);
            this._cursorChangedId = null;
        }
        
        // Cancel any pending timeout
        if (this._handCursorTimeoutId) {
            GLib.Source.remove(this._handCursorTimeoutId);
            this._handCursorTimeoutId = null;
        }
        
        this._cursorTracker = null;
        this._lastSprite = null;
        this._isHandCursor = false;
        this._hapticTriggered = false;
        this._handCursorStartTime = null;
        this._waveform = DEFAULT_WAVEFORM;
        
        log('[HapticCursor] Extension disabled');
    }

    _startPolling() {
        if (this._pollTimeoutId) {
            return;
        }
        
        this._pollTimeoutId = GLib.timeout_add(
            GLib.PRIORITY_DEFAULT,
            CURSOR_CHECK_INTERVAL_MS,
            () => {
                this._checkCursor();
                return GLib.SOURCE_CONTINUE;
            }
        );
    }

    _stopPolling() {
        if (this._pollTimeoutId) {
            GLib.Source.remove(this._pollTimeoutId);
            this._pollTimeoutId = null;
        }
    }

    _loadSettings() {
        try {
            const file = Gio.File.new_for_path(SETTINGS_FILE_PATH);
            
            if (!file.query_exists(null)) {
                log(`[HapticCursor] Settings file not found at ${SETTINGS_FILE_PATH}, using default waveform`);
                this._waveform = DEFAULT_WAVEFORM;
                return;
            }
            
            const [success, contents] = file.load_contents(null);
            
            if (!success) {
                log('[HapticCursor] Failed to read settings file, using default waveform');
                this._waveform = DEFAULT_WAVEFORM;
                return;
            }
            
            const decoder = new TextDecoder('utf-8');
            const text = decoder.decode(contents);
            
            // Parse JSON
            const settings = JSON.parse(text);
            
            if (settings && settings.cursor && settings.cursor.link_wave) {
                const waveform = settings.cursor.link_wave;
                this._waveform = waveform;
                log(`[HapticCursor] Loaded cursor waveform from settings: ${waveform}`);
            } else {
                log('[HapticCursor] No cursor.link_wave found in settings, using default waveform');
                this._waveform = DEFAULT_WAVEFORM;
            }
        } catch (e) {
            logError(e, '[HapticCursor] Error loading settings file');
            this._waveform = DEFAULT_WAVEFORM;
        }
    }

    _setupSettingsMonitor() {
        try {
            const file = Gio.File.new_for_path(SETTINGS_FILE_PATH);
            
            // Create parent directory monitoring if file doesn't exist yet
            const parentDir = file.get_parent();
            
            if (!parentDir.query_exists(null)) {
                log('[HapticCursor] Settings directory does not exist, skipping file monitoring');
                return;
            }
            
            this._settingsFileMonitor = file.monitor_file(Gio.FileMonitorFlags.NONE, null);
            
            this._settingsMonitorId = this._settingsFileMonitor.connect('changed', 
                (monitor, file, otherFile, eventType) => {
                    if (eventType === Gio.FileMonitorEvent.CHANGES_DONE_HINT ||
                        eventType === Gio.FileMonitorEvent.CREATED ||
                        eventType === Gio.FileMonitorEvent.DELETED) {
                        log('[HapticCursor] Settings file changed, reloading...');
                        this._loadSettings();
                    }
                }
            );
            
            log(`[HapticCursor] Monitoring settings file: ${SETTINGS_FILE_PATH}`);
        } catch (e) {
            logError(e, '[HapticCursor] Error setting up settings file monitor');
        }
    }

    _cleanupSettingsMonitor() {
        if (this._settingsMonitorId && this._settingsFileMonitor) {
            this._settingsFileMonitor.disconnect(this._settingsMonitorId);
            this._settingsMonitorId = null;
        }
        
        if (this._settingsFileMonitor) {
            this._settingsFileMonitor.cancel();
            this._settingsFileMonitor = null;
        }
    }

    _onCursorChanged() {
        // Cursor changed - check it immediately
        this._checkCursor();
    }

    _checkCursor() {
        // Get cursor sprite to detect changes
        const sprite = this._cursorTracker.get_sprite();
        
        // Detect if this looks like a hand cursor by checking sprite properties
        // Hand cursors typically have specific dimensions
        const isHandCursor = this._detectHandCursor(sprite);
        
        if (isHandCursor && !this._isHandCursor) {
            // Cursor just became a hand - ONLY trigger on ENTERING clickable area
            log('[HapticCursor] Entered clickable area (hand cursor detected)');
            this._isHandCursor = true;
            this._handCursorStartTime = GLib.get_monotonic_time();
            this._hapticTriggered = false;
            
        } else if (!isHandCursor && this._isHandCursor) {
            // Cursor is no longer a hand - just reset state, NO haptic trigger
            log('[HapticCursor] Left clickable area (hand cursor removed)');
            this._isHandCursor = false;
            this._handCursorStartTime = null;
            this._hapticTriggered = false;
            // DO NOT trigger haptic here - we only want feedback when ENTERING
            
        } else if (isHandCursor && this._isHandCursor && !this._hapticTriggered) {
            // Still over hand cursor - check if we've been here long enough
            const elapsed = (GLib.get_monotonic_time() - this._handCursorStartTime) / 1000;
            if (elapsed >= HAND_CURSOR_DELAY_MS) {
                // Only trigger after sustained hover on clickable element
                this._triggerHapticFeedback();
            }
        }
        
        this._lastSprite = sprite;
    }

    _detectHandCursor(sprite) {
        if (!sprite) {
            return false;
        }
        
        // Get sprite dimensions
        const width = sprite.get_width();
        const height = sprite.get_height();
        
        // Get the hot spot (click point) of the cursor
        const [hotX, hotY] = this._cursorTracker.get_hot();
        
        // Hand/pointer cursor has very specific characteristics:
        // - Size typically 32x32 or 48x48 at 1x scale (64x64 or 96x96 at 2x)
        // - Hot spot is at the tip of the finger (usually around 1/4 from left, 1/5 from top)
        // - Aspect ratio very close to 1:1
        // - Not too small (excludes arrow), not too large (excludes loading spinners)
        
        // Default arrow cursor is typically 24x36 or 32x48 (taller than wide)
        // Hand cursor is typically 32x32 or 48x48 (square-ish)
        // I-beam/text cursor is very thin and tall
        // Loading cursor can be large and circular
        
        const aspectRatio = width / height;
        
        // Hand cursor is nearly square (0.9 - 1.1 aspect ratio)
        // Arrow cursor is taller (0.6-0.7), I-beam is very thin (<0.3)
        if (aspectRatio < 0.85 || aspectRatio > 1.15) {
            return false;
        }
        
        // Hand cursor size is medium (not tiny arrow, not huge loading)
        // At 1x scale: 28-52 pixels, at 2x scale: 56-104 pixels
        const minDimension = Math.min(width, height);
        const maxDimension = Math.max(width, height);
        
        if (minDimension < 28 || maxDimension > 104) {
            return false;
        }
        
        // Hot spot for hand cursor is typically near the finger tip
        // This is roughly at (1/4, 1/5) from top-left
        // Arrow cursor hot spot is at tip (0, 0)
        // I-beam hot spot is centered vertically
        const hotXRatio = hotX / width;
        const hotYRatio = hotY / height;
        
        // Hand cursor hot spot is NOT at the corner (like arrow)
        // and NOT centered (like I-beam)
        // Typically between 0.15-0.35 horizontally and 0.1-0.25 vertically
        const isHandHotSpot = (hotXRatio >= 0.12 && hotXRatio <= 0.4) &&
                              (hotYRatio >= 0.08 && hotYRatio <= 0.3);
        
        if (!isHandHotSpot) {
            return false;
        }
        
        // Additional check: size should be consistent (relatively square)
        const sizeDiff = Math.abs(width - height);
        if (sizeDiff > 8) {  // Allow small variation but not arrow-like proportions
            return false;
        }
        
        log(`[HapticCursor] Cursor detected: ${width}x${height}, hot=(${hotX},${hotY}), ratios=(${hotXRatio.toFixed(2)},${hotYRatio.toFixed(2)}), aspect=${aspectRatio.toFixed(2)}`);
        
        return true;
    }

    _triggerHapticFeedback() {
        // Only trigger once per continuous hand cursor session
        if (this._hapticTriggered) {
            return;
        }
        
        this._hapticTriggered = true;
        
        log(`[HapticCursor] Triggering haptic feedback with waveform: ${this._waveform}`);
        
        try {
            // Call the haptic D-Bus service
            const connection = Gio.DBus.session;
            
            connection.call(
                DBUS_NAME,
                DBUS_PATH,
                DBUS_INTERFACE,
                'PlayWaveform',
                new GLib.Variant('(s)', [this._waveform]),
                null,
                Gio.DBusCallFlags.NONE,
                -1,
                null,
                (conn, result) => {
                    try {
                        const reply = conn.call_finish(result);
                        log(`[HapticCursor] Haptic feedback triggered successfully: ${reply.print(true)}`);
                    } catch (e) {
                        logError(e, '[HapticCursor] Failed to trigger haptic feedback');
                    }
                }
            );
        } catch (e) {
            logError(e, '[HapticCursor] Error calling haptic D-Bus service');
        }
    }
}
