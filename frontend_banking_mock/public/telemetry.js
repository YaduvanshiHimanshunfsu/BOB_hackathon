/**
 * telemetry.js
 * ============
 * Client-side Behavioral & Device Telemetry Collection Engine.
 * 
 * Implements Fix 4:
 * - Passive background collection every 30 seconds.
 * - Active event-triggered collection on critical actions (login, transfer).
 * 
 * Implements Fix 2:
 * - Removed AES-256 client-side encryption. Relies entirely on TLS 1.3
 *   transport security.
 */

class TelemetryEngine {
    constructor(apiUrl, userId, sessionId) {
        this.apiUrl = apiUrl;
        this.userId = userId;
        this.sessionId = sessionId;
        
        // Behavioral buffers
        this.keystrokes = [];
        this.mouseEvents = [];
        this.scrollDeltas = [];
        
        // State
        this.lastKeyPress = 0;
        this.passiveIntervalId = null;
        this.deviceFingerprint = null;
        
        this.PASSIVE_INTERVAL_MS = 30000; // 30 seconds
    }

    async init() {
        this.deviceFingerprint = await this.generateDeviceFingerprint();
        this.startTracking();
        this.startPassivePolling();
        
        // Send initial payload
        await this.flush("session_start");
    }

    // --- Device Fingerprinting (Weighted Jaccard targets) ---
    async generateDeviceFingerprint() {
        return {
            canvas_hash: this.getCanvasHash(),
            webgl_renderer: this.getWebGLRenderer(),
            audio_hash: await this.getAudioHash(),
            screen: `${window.screen.width}x${window.screen.height}x${window.screen.colorDepth}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            user_agent: navigator.userAgent,
            fonts_hash: this.getFontsHash()
        };
    }

    getCanvasHash() {
        try {
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
            ctx.textBaseline = "top";
            ctx.font = "14px 'Arial'";
            ctx.textBaseline = "alphabetic";
            ctx.fillStyle = "#f60";
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = "#069";
            ctx.fillText("Bank of Baroda 🏦", 2, 15);
            ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
            ctx.fillText("Bank of Baroda 🏦", 4, 17);
            
            // Simple hash
            let str = canvas.toDataURL();
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                hash = ((hash << 5) - hash) + str.charCodeAt(i);
                hash |= 0;
            }
            return hash.toString(16);
        } catch (e) {
            return "canvas_error";
        }
    }

    getWebGLRenderer() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            const ext = gl.getExtension('WEBGL_debug_renderer_info');
            return gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
        } catch (e) {
            return "webgl_error";
        }
    }

    async getAudioHash() {
        // Simplified mockup for audio stack hash
        return "audio_hash_mock_12345";
    }
    
    getFontsHash() {
        return "fonts_hash_mock_54321";
    }

    // --- Behavioral Tracking ---
    startTracking() {
        // Keystrokes
        document.addEventListener('keydown', (e) => {
            this.lastKeyPress = Date.now();
        });
        
        document.addEventListener('keyup', (e) => {
            const now = Date.now();
            const holdTime = now - this.lastKeyPress;
            const flightTime = this.keystrokes.length > 0 
                ? now - this.keystrokes[this.keystrokes.length - 1].timestamp 
                : 0;
                
            this.keystrokes.push({
                key_code: e.keyCode,
                hold_ms: holdTime,
                flight_ms: flightTime,
                timestamp: now
            });
        });

        // Mouse (Throttle to avoid blowing up memory)
        let lastMouseTime = 0;
        let lastMouseX = 0;
        let lastMouseY = 0;
        
        document.addEventListener('mousemove', (e) => {
            const now = Date.now();
            if (now - lastMouseTime > 50) { // Every 50ms max
                const dx = e.clientX - lastMouseX;
                const dy = e.clientY - lastMouseY;
                const dist = Math.sqrt(dx*dx + dy*dy);
                const velocity = (now - lastMouseTime) > 0 ? dist / (now - lastMouseTime) : 0;
                
                this.mouseEvents.push({
                    x: e.clientX,
                    y: e.clientY,
                    velocity: velocity,
                    timestamp: now
                });
                
                lastMouseX = e.clientX;
                lastMouseY = e.clientY;
                lastMouseTime = now;
            }
        });

        // Scrolling
        document.addEventListener('wheel', (e) => {
            this.scrollDeltas.push(e.deltaY);
        });
    }

    // --- Ingestion ---
    startPassivePolling() {
        this.passiveIntervalId = setInterval(() => {
            this.flush("passive");
        }, this.PASSIVE_INTERVAL_MS);
    }

    async triggerEvent(eventName) {
        // Explicitly trigger a payload flush for critical events
        await this.flush(eventName);
    }

    async flush(eventTrigger) {
        if (!this.deviceFingerprint) return;

        const payload = {
            session_id: this.sessionId,
            user_id: this.userId,
            timestamp: Date.now(),
            event_trigger: eventTrigger,
            device: this.deviceFingerprint,
            behavioral: {
                keystrokes: this.keystrokes.splice(0, 500), // Pop from buffer
                mouse_events: this.mouseEvents.splice(0, 1000),
                scroll_delta_y: this.scrollDeltas.splice(0, 200),
                touch_pressure: []
            }
        };

        try {
            // FIX 2: Sent as plain JSON over TLS 1.3
            await fetch(`${this.apiUrl}/api/v1/telemetry/ingest`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        } catch (error) {
            console.error("Telemetry ingestion failed:", error);
        }
    }
}

window.TelemetryEngine = TelemetryEngine;
