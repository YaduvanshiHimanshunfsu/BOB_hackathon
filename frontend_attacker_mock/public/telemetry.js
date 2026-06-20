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
        this.passiveIntervalId = null;
        this.deviceFingerprint = null;
        
        this.PASSIVE_INTERVAL_MS = 30000; // 30 seconds

        // Bind event handlers so they can be removed later
        this.handleKeyDown = this.handleKeyDown.bind(this);
        this.handleKeyUp = this.handleKeyUp.bind(this);
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleWheel = this.handleWheel.bind(this);
        
        this.lastKeyPress = 0;
        this.lastMouseTime = 0;
        this.lastMouseX = 0;
        this.lastMouseY = 0;
    }

    async init() {
        this.deviceFingerprint = await this.generateDeviceFingerprint();
        
        document.addEventListener('keydown', this.handleKeyDown);
        document.addEventListener('keyup', this.handleKeyUp);
        document.addEventListener('mousemove', this.handleMouseMove);
        document.addEventListener('wheel', this.handleWheel);

        this.startPassivePolling();
        
        // Send initial payload
        await this.flush("session_start");
    }

    stop() {
        if (this.passiveIntervalId) {
            clearInterval(this.passiveIntervalId);
            this.passiveIntervalId = null;
        }
        document.removeEventListener('keydown', this.handleKeyDown);
        document.removeEventListener('keyup', this.handleKeyUp);
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('wheel', this.handleWheel);
    }

    // --- Device Fingerprinting (Weighted Jaccard targets) ---
    async generateDeviceFingerprint() {
        return {
            canvas_hash: "spoofed_attacker_canvas_hash_0987654321",
            webgl_renderer: "ANGLE (Software Adapter)",
            audio_hash: "spoofed_attacker_audio_hash_0987654321",
            screen: "1366x768x24",
            timezone: "Europe/Moscow",
            language: "ru-RU",
            user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            fonts_hash: "0011001100"
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
            if (!gl) return "no_webgl";
            const ext = gl.getExtension('WEBGL_debug_renderer_info');
            if (!ext) return "no_debug_renderer";
            return gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
        } catch (e) {
            return "webgl_error";
        }
    }

    async getAudioHash() {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioCtx.createOscillator();
            const analyser = audioCtx.createAnalyser();
            const gain = audioCtx.createGain();
            const scriptProcessor = audioCtx.createScriptProcessor(4096, 1, 1);

            gain.gain.value = 0; // Mute it
            oscillator.type = "triangle";
            oscillator.connect(analyser);
            analyser.connect(scriptProcessor);
            scriptProcessor.connect(gain);
            gain.connect(audioCtx.destination);

            oscillator.start(0);
            return new Promise((resolve) => {
                scriptProcessor.onaudioprocess = function () {
                    oscillator.stop();
                    scriptProcessor.disconnect();
                    audioCtx.close();
                    
                    const data = new Float32Array(analyser.frequencyBinCount);
                    analyser.getFloatFrequencyData(data);
                    
                    // Generate a simple hash from the frequency data
                    let hash = 0;
                    for (let i = 0; i < data.length; i++) {
                        hash = ((hash << 5) - hash) + data[i];
                        hash |= 0;
                    }
                    resolve(hash.toString(16));
                };
            });
        } catch (e) {
            return "audio_error";
        }
    }
    
    getFontsHash() {
        // Simple DOM-based font detection fingerprint
        const baseFonts = ['monospace', 'sans-serif', 'serif'];
        const testFonts = ['Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana', 'Georgia', 'Comic Sans MS', 'Trebuchet MS', 'Arial Black', 'Impact'];
        
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const text = "abcdefghijklmnopqrstuvwxyz0123456789";
        
        let hashStr = "";
        for (const font of testFonts) {
            let detected = false;
            for (const baseFont of baseFonts) {
                ctx.font = `72px ${baseFont}`;
                const baselineWidth = ctx.measureText(text).width;
                
                ctx.font = `72px '${font}', ${baseFont}`;
                const testWidth = ctx.measureText(text).width;
                
                if (testWidth !== baselineWidth) {
                    detected = true;
                    break;
                }
            }
            hashStr += detected ? "1" : "0";
        }
        return hashStr;
    }

    // --- Behavioral Tracking ---
    handleKeyDown(e) {
        this.lastKeyPress = Date.now();
    }

    handleKeyUp(e) {
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
    }

    handleMouseMove(e) {
        const now = Date.now();
        if (now - this.lastMouseTime > 50) { // Every 50ms max
            const dx = e.clientX - this.lastMouseX;
            const dy = e.clientY - this.lastMouseY;
            const dist = Math.sqrt(dx*dx + dy*dy);
            const velocity = (now - this.lastMouseTime) > 0 ? dist / (now - this.lastMouseTime) : 0;
            
            this.mouseEvents.push({
                x: e.clientX,
                y: e.clientY,
                velocity: velocity,
                timestamp: now
            });
            
            this.lastMouseX = e.clientX;
            this.lastMouseY = e.clientY;
            this.lastMouseTime = now;
        }
    }

    handleWheel(e) {
        this.scrollDeltas.push(e.deltaY);
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
            const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
            navigator.sendBeacon(`${this.apiUrl}/api/v1/telemetry/ingest`, blob);
        } catch (error) {
            console.error("Telemetry ingestion failed:", error);
        }
    }
}

window.TelemetryEngine = TelemetryEngine;
