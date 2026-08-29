import React, { useState, useEffect, useRef } from "react";
import Navbar from "./components/Navbar";
import LiveMonitorTab from "./components/LiveMonitorTab";
import TrajectoryTab from "./components/TrajectoryTab";
import AnalyticsTab from "./components/AnalyticsTab";
import AlertsTab from "./components/AlertsTab";
import { api, connectWebSocket } from "./services/api";

export default function App() {
  const [activeTab, setActiveTab] = useState("LIVE_MONITOR");
  const [wsConnected, setWsConnected] = useState(false);
  const [simRunning, setSimRunning] = useState(false);

  // Core Real-Time State
  const [cameras, setCameras] = useState([]);
  const [recentDetections, setRecentDetections] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [selectedPlateForTrajectory, setSelectedPlateForTrajectory] = useState("DL01AB1234");
  const [toastAlert, setToastAlert] = useState(null);

  // 1. Initial Data Fetch
  useEffect(() => {
    async function initData() {
      try {
        const [cams, dets, alrts, simStatus] = await Promise.all([
          api.getCameras(),
          api.getRecentDetections(25),
          api.getAlerts(false),
          api.getSimulationStatus()
        ]);
        setCameras(cams);
        setRecentDetections(dets);
        setAlerts(alrts);
        setSimRunning(simStatus.running);
      } catch (err) {
        console.error("Initialization error:", err);
      }
    }
    initData();
  }, []);

  // 2. Real-Time WebSocket Listener
  useEffect(() => {
    const wsClient = connectWebSocket(
      (message) => {
        if (message.event === "DETECTION") {
          setRecentDetections((prev) => [message.data, ...prev.slice(0, 40)]);
        } else if (message.event === "ALERT") {
          setAlerts((prev) => [message.data, ...prev]);
          // Trigger floating toast alert for hotlist hits
          setToastAlert(message.data);
          setTimeout(() => setToastAlert(null), 6000);
        }
      },
      (connected) => {
        setWsConnected(connected);
      }
    );

    return () => {
      wsClient.disconnect();
    };
  }, []);

  // 3. Handlers
  const handleToggleSim = async () => {
    try {
      if (simRunning) {
        await api.stopSimulation();
        setSimRunning(false);
      } else {
        await api.startSimulation();
        setSimRunning(true);
      }
    } catch (err) {
      console.error("Failed to toggle simulation:", err);
    }
  };

  const handleTriggerStep = async () => {
    try {
      await api.triggerSimulationStep();
    } catch (err) {
      console.error("Failed to trigger simulation step:", err);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await api.resolveAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, is_resolved: true } : a))
      );
    } catch (err) {
      console.error("Failed to resolve alert:", err);
    }
  };

  const handleSelectPlateForTrajectory = (plate) => {
    setSelectedPlateForTrajectory(plate);
    setActiveTab("TRAJECTORY");
  };

  const unresolvedAlerts = alerts.filter((a) => !a.is_resolved);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Command Center Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        wsConnected={wsConnected}
        simRunning={simRunning}
        onToggleSim={handleToggleSim}
        onTriggerStep={handleTriggerStep}
        unresolvedAlertCount={unresolvedAlerts.length}
      />

      {/* Floating Hotlist Match Toast Notification */}
      {toastAlert && (
        <div className="fixed top-16 right-4 z-50 max-w-sm glass-card p-4 border border-red-500 shadow-2xl shadow-red-500/30 animate-bounce">
          <div className="flex items-center justify-between text-red-400 font-bold text-xs">
            <span>🚨 REAL-TIME SECURITY ALARM</span>
            <button
              onClick={() => setToastAlert(null)}
              className="text-slate-400 hover:text-slate-200"
            >
              ✕
            </button>
          </div>
          <div className="mt-1 text-sm font-mono font-bold text-white">
            {toastAlert.plate_number} detected at {toastAlert.camera_name || toastAlert.camera_id}
          </div>
          <div className="mt-1 text-xs text-slate-300">
            {toastAlert.message}
          </div>
          <div className="mt-2 flex justify-end">
            <button
              onClick={() => handleSelectPlateForTrajectory(toastAlert.plate_number)}
              className="px-2.5 py-1 bg-red-600 hover:bg-red-500 text-white font-bold text-[11px] rounded transition-all shadow"
            >
              Track Trajectory Now
            </button>
          </div>
        </div>
      )}

      {/* Main Tab Content View */}
      <main className="container-full flex-1 py-4">
        {activeTab === "LIVE_MONITOR" && (
          <LiveMonitorTab
            cameras={cameras}
            recentDetections={recentDetections}
            onSelectPlateForTrajectory={handleSelectPlateForTrajectory}
            activeAlerts={unresolvedAlerts}
          />
        )}

        {activeTab === "TRAJECTORY" && (
          <TrajectoryTab
            initialPlate={selectedPlateForTrajectory}
            cameras={cameras}
          />
        )}

        {activeTab === "ANALYTICS" && <AnalyticsTab />}

        {activeTab === "ALERTS" && (
          <AlertsTab
            alerts={alerts}
            onResolveAlert={handleResolveAlert}
            onSelectPlateForTrajectory={handleSelectPlateForTrajectory}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-3 text-center text-xs text-slate-500">
        <div className="container-full flex items-center justify-between">
          <span>NETRADEEP Central ANPR Intelligence Engine • SIH 2026 Prototype</span>
          <span className="font-mono">Node Latency: ~14ms | 4K PTZ Stream Ready</span>
        </div>
      </footer>
    </div>
  );
}
