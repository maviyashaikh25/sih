const host = typeof window !== "undefined" && window.location.hostname ? window.location.hostname : "127.0.0.1";
const API_BASE = `http://${host}:8000/api/v1`;
const WS_URL = `ws://${host}:8000/ws/live`;

export const api = {
  // Cameras
  async getCameras() {
    const res = await fetch(`${API_BASE}/cameras/`);
    if (!res.ok) throw new Error("Failed to fetch cameras");
    return res.json();
  },

  async getCameraRecentDetections(cameraId, limit = 10) {
    const res = await fetch(`${API_BASE}/cameras/${cameraId}/recent_detections?limit=${limit}`);
    if (!res.ok) throw new Error("Failed to fetch camera detections");
    return res.json();
  },

  // Detections
  async getRecentDetections(limit = 30) {
    const res = await fetch(`${API_BASE}/detections/recent?limit=${limit}`);
    if (!res.ok) throw new Error("Failed to fetch recent detections");
    return res.json();
  },

  async ingestDetection(payload) {
    const res = await fetch(`${API_BASE}/detections/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to ingest detection");
    return res.json();
  },

  // Trajectories
  async queryTrajectory(plateNumber) {
    const res = await fetch(`${API_BASE}/trajectories/query?plate=${encodeURIComponent(plateNumber)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `No trajectory found for ${plateNumber}`);
    }
    return res.json();
  },

  async getActivePlates(limit = 10) {
    const res = await fetch(`${API_BASE}/trajectories/active_plates?limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  },

  async simulatePlateTrajectory(plateNumber) {
    const res = await fetch(`${API_BASE}/trajectories/simulate?plate=${encodeURIComponent(plateNumber)}`, {
      method: "POST"
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to simulate trajectory");
    }
    return res.json();
  },

  // Analytics
  async getMacroAnalytics() {
    const res = await fetch(`${API_BASE}/analytics/macro`);
    if (!res.ok) throw new Error("Failed to fetch analytics");
    return res.json();
  },

  // Alerts & Blacklist
  async getAlerts(unresolvedOnly = false) {
    const res = await fetch(`${API_BASE}/alerts/?unresolved_only=${unresolvedOnly}`);
    if (!res.ok) throw new Error("Failed to fetch alerts");
    return res.json();
  },

  async resolveAlert(alertId, officerName = "Control Room Officer") {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/resolve?officer_name=${encodeURIComponent(officerName)}`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Failed to resolve alert");
    return res.json();
  },

  async getBlacklist() {
    const res = await fetch(`${API_BASE}/alerts/blacklist`);
    if (!res.ok) throw new Error("Failed to fetch blacklist");
    return res.json();
  },

  async addToBlacklist(payload) {
    const res = await fetch(`${API_BASE}/alerts/blacklist`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to add plate to blacklist");
    return res.json();
  },

  async removeFromBlacklist(plateNumber) {
    const res = await fetch(`${API_BASE}/alerts/blacklist/${encodeURIComponent(plateNumber)}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Failed to remove plate from blacklist");
    return res.json();
  },

  // Simulation
  async startSimulation() {
    const res = await fetch(`${API_BASE}/simulation/start`, { method: "POST" });
    return res.json();
  },

  async stopSimulation() {
    const res = await fetch(`${API_BASE}/simulation/stop`, { method: "POST" });
    return res.json();
  },

  async getSimulationStatus() {
    const res = await fetch(`${API_BASE}/simulation/status`);
    return res.json();
  },

  async triggerSimulationStep() {
    const res = await fetch(`${API_BASE}/simulation/trigger_step`, { method: "POST" });
    return res.json();
  },

  // Custom Feed Upload
  async uploadCameraFeed(formData) {
    const res = await fetch(`${API_BASE}/feed/upload`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to upload and process feed");
    }
    return res.json();
  }
};

export function connectWebSocket(onMessage, onStatusChange) {
  let ws = null;
  let reconnectTimer = null;
  let isClosedExplicitly = false;

  function connect() {
    if (isClosedExplicitly) return;
    try {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log("[WS] Connected to Live ANPR Stream");
        if (onStatusChange) onStatusChange(true);
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          if (onMessage) onMessage(parsed);
        } catch (e) {
          console.warn("[WS] Error parsing message:", e);
        }
      };

      ws.onerror = () => {
        if (!isClosedExplicitly && onStatusChange) onStatusChange(false);
      };

      ws.onclose = () => {
        if (onStatusChange) onStatusChange(false);
        if (!isClosedExplicitly) {
          console.log("[WS] Disconnected. Reconnecting in 3s...");
          clearTimeout(reconnectTimer);
          reconnectTimer = setTimeout(connect, 3000);
        }
      };
    } catch (e) {
      if (onStatusChange) onStatusChange(false);
      if (!isClosedExplicitly) {
        reconnectTimer = setTimeout(connect, 3000);
      }
    }
  }

  connect();

  return {
    disconnect: () => {
      isClosedExplicitly = true;
      clearTimeout(reconnectTimer);
      if (ws) {
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => {
            try { ws.close(); } catch (_) {}
          };
        } else if (ws.readyState === WebSocket.OPEN) {
          try { ws.close(); } catch (_) {}
        }
      }
    }
  };
}
