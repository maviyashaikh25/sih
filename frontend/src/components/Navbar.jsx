import React from "react";
import { 
  ShieldAlert, 
  Cctv, 
  Route, 
  BarChart3, 
  Radio, 
  Play, 
  Square, 
  Zap, 
  Bell,
  Cpu
} from "lucide-react";

export default function Navbar({
  activeTab,
  setActiveTab,
  wsConnected,
  simRunning,
  onToggleSim,
  onTriggerStep,
  unresolvedAlertCount = 0
}) {
  const tabs = [
    { id: "LIVE_MONITOR", label: "Live Multi-Camera Monitor", icon: Cctv },
    { id: "TRAJECTORY", label: "Vehicle Trajectory Tracker", icon: Route },
    { id: "ANALYTICS", label: "Macro Traffic Analytics", icon: BarChart3 },
    { id: "ALERTS", label: "Hotlist & Alert Center", icon: ShieldAlert, badge: unresolvedAlertCount },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50 px-4 py-3">
      <div className="container-full flex flex-wrap items-center justify-between gap-4">
        {/* Left: Branding & Status */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Cpu className="w-6 h-6 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-wider text-slate-100 font-heading">
                NETRA<span className="text-cyan-400">DEEP</span>
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                ANPR AI v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              City-Wide Multi-Camera Surveillance & Spatial-Temporal Tracking
            </p>
          </div>
        </div>

        {/* Center: Main Navigation Tabs */}
        <nav className="flex items-center gap-1.5 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all relative ${
                  isActive
                    ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : "text-slate-400"}`} />
                <span>{tab.label}</span>
                {tab.badge > 0 && (
                  <span className="ml-1 px-1.5 py-0.2 bg-red-500 text-white rounded-full text-[10px] font-bold animate-pulse">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right: Live Stream Status & Simulation Controls */}
        <div className="flex items-center gap-3">
          {/* WebSocket Status Indicator */}
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                wsConnected ? "bg-emerald-400 shadow-sm shadow-emerald-400 animate-ping" : "bg-red-500"
              }`}
            />
            <span className={wsConnected ? "text-emerald-400 font-medium" : "text-red-400 font-medium"}>
              {wsConnected ? "LIVE STREAM ACTIVE" : "STREAM OFFLINE"}
            </span>
          </div>

          {/* Quick Simulation Trigger */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={onToggleSim}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                simRunning
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/50 hover:bg-amber-500/30"
                  : "bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700"
              }`}
            >
              {simRunning ? <Square className="w-3.5 h-3.5 fill-amber-400 text-amber-400" /> : <Play className="w-3.5 h-3.5 text-cyan-400" />}
              <span>{simRunning ? "Stop City Flow" : "Simulate Flow"}</span>
            </button>

            <button
              onClick={onTriggerStep}
              title="Inject instant live ANPR detection event"
              className="p-1.5 rounded-lg bg-slate-800 text-cyan-400 border border-slate-700 hover:bg-cyan-500/20 hover:border-cyan-500/40 transition-all"
            >
              <Zap className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
