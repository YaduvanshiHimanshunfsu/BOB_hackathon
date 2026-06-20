import { useEffect, useState } from 'react';

export function useTelemetry(userId, sessionId) {
  const [engine, setEngine] = useState(null);

  useEffect(() => {
    // Wait for the global script to be ready
    if (window.TelemetryEngine && userId && sessionId) {
      const apiHost = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const te = new window.TelemetryEngine(apiHost, userId, sessionId);
      te.init();
      setEngine(te);
      console.log("Telemetry Engine Initialized:", userId, sessionId);

      return () => {
        te.stop();
      };
    }
  }, [userId, sessionId]);

  const triggerEvent = async (eventName) => {
    if (engine) {
      await engine.triggerEvent(eventName);
    }
  };

  return { triggerEvent };
}
