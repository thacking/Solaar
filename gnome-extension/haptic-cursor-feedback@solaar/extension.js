// extension.js - Haptic Cursor Feedback Extension for GNOME Shell 47/48
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Meta from 'gi://Meta';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const HAND_CURSOR_DELAY_MS = 20;
const CURSOR_CHECK_INTERVAL_MS = 20; // Check cursor every 50ms
const DBUS_NAME = 'io.github.pwr_solaar.Haptics';
const DBUS_PATH = '/io/github/pwr_solaar/Haptics';
const DBUS_INTERFACE = 'io.github.pwr_solaar.Haptics';
const WAVEFORM = 'DAMP COLLISION';

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
    }

    enable() {
        log('[HapticCursor] Enabling extension');
        
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
        
        // Hand cursors are typically larger than default arrow cursor
        // Default cursor is usually 24x24 or 32x32
        // Hand cursor is usually 32x32 or larger with different aspect ratio
        // This is a heuristic - may need tuning
        
        // Check if cursor is reasonably large (hand cursors tend to be 24-48 pixels)
        const minSize = 20;
        const maxSize = 64;
        
        if (width < minSize || height < minSize || width > maxSize || height > maxSize) {
            return false;
        }
        
        // Hand cursors often have aspect ratio close to 1:1 but slightly taller
        const aspectRatio = width / height;
        
        // Hand cursor heuristic: medium size with aspect ratio between 0.7 and 1.3
        // and total area suggesting it's not the default small arrow
        const area = width * height;
        const isLikelyHand = (aspectRatio >= 0.7 && aspectRatio <= 1.3) && (area >= 600);
        
        return isLikelyHand;
    }

    _triggerHapticFeedback() {
        // Only trigger once per continuous hand cursor session
        if (this._hapticTriggered) {
            return;
        }
        
        this._hapticTriggered = true;
        
        log('[HapticCursor] Triggering haptic feedback');
        
        try {
            // Call the haptic D-Bus service
            const connection = Gio.DBus.session;
            
            connection.call(
                DBUS_NAME,
                DBUS_PATH,
                DBUS_INTERFACE,
                'PlayWaveform',
                new GLib.Variant('(s)', [WAVEFORM]),
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
