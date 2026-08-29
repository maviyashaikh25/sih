import React, { useState } from "react";
import { 
  Cctv, 
  Car, 
  Clock, 
  MapPin, 
  ShieldAlert, 
  Activity, 
  Search, 
  ArrowRight,
  Maximize2,
  CheckCircle2,
  Radio
} from "lucide-react";

export default function LiveMonitorTab({
  cameras = [],
  recentDetections = [],
  onSelectPlateForTrajectory,
  activeAlerts = []
}) {
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.id || "CAM_CP_01");
  const [gridCount, setGridCount] = useState(4);

  const selectedCam = cameras.find(c => c.id === selectedCameraId) || cameras[0];
  const displayCameras = cameras.slice(0, gridCount);

  return (
    <div className="space-y-4">
      {/* Top Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="glass-card p-3.5 border-l-4 border-l-cyan-400">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Detections Monitored Today</span>
            <Car className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100 font-heading">
              {(recentDetections.length * 14 + 342).toLocaleString()}
            </span>
            <span className="text-xs text-emerald-400 flex items-center font-medium">+14.8% vs avg</span>
          </div>
        </div>

        <div className="glass-card p-3.5 border-l-4 border-l-blue-400">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active City Cameras</span>
            <Cctv className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100 font-heading">
              {cameras.length} / {cameras.length}
            </span>
            <span className="text-xs text-emerald-400 font-medium">100% Operational</span>
          </div>
        </div>

        <div className="glass-card p-3.5 border-l-4 border-l-amber-400">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Avg Network Speed</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100 font-heading">44.8 km/h</span>
            <span className="text-xs text-slate-400">Moderate Flow</span>
          </div>
        </div>

        <div className="glass-card p-3.5 border-l-4 border-l-red-500">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Security Alerts</span>
            <ShieldAlert className="w-4 h-4 text-red-500 animate-pulse" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-red-400 font-heading">
              {activeAlerts.length}
            </span>
            <span className="text-xs text-red-400 font-medium">Hotlist Triggered</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Multi-Camera Wall & Live ANPR Detection Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left 2 Cols: CCTV Video Stream Wall */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Live Video Surveillance Wall
              </h2>
            </div>
            
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-slate-400 mr-1">Grid Layout:</span>
              {[4, 6].map((num) => (
                <button
                  key={num}
                  onClick={() => setGridCount(num)}
                  className={`px-2 py-0.5 rounded font-medium transition-all ${
                    gridCount === num
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                  }`}
                >
                  {num} Feeds
                </button>
              ))}
            </div>
          </div>

          <div className={`grid ${gridCount === 4 ? "grid-cols-2" : "grid-cols-3"} gap-3`}>
            {displayCameras.map((cam, idx) => {
              const isSelected = cam.id === selectedCameraId;
              const hasAlert = activeAlerts.some(a => a.camera_id === cam.id && !a.is_resolved);

              return (
                <div
                  key={cam.id}
                  onClick={() => setSelectedCameraId(cam.id)}
                  className={`relative rounded-xl overflow-hidden cursor-pointer transition-all border ${
                    hasAlert
                      ? "border-red-500 shadow-md shadow-red-500/20"
                      : isSelected
                      ? "border-cyan-400 shadow-md shadow-cyan-500/20"
                      : "border-slate-800 hover:border-slate-700"
                  }`}
                >
                  {/* Simulated Camera Video Frame Canvas */}
                  <div className="aspect-video bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 flex flex-col justify-between p-2.5 relative overflow-hidden">
                    {/* Simulated road / perspective lines */}
                    <div className="absolute inset-0 opacity-15 pointer-events-none">
                      <div className="w-full h-1/2 border-b border-cyan-400/40 mt-12" />
                      <div className="w-full h-1/2 border-b border-dashed border-cyan-400/30" />
                    </div>

                    {/* Top Overlay: Camera Title & Status Badge */}
                    <div className="flex items-center justify-between z-10">
                      <div className="flex items-center gap-1.5 bg-slate-950/80 px-2 py-0.5 rounded border border-slate-700 text-[10px] text-cyan-300 font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                        <span>{cam.id}</span>
                      </div>
                      <span className="text-[10px] bg-slate-900/90 text-slate-300 px-1.5 py-0.5 rounded font-mono">
                        {cam.fps} FPS | 4K
                      </span>
                    </div>

                    {/* Center: Live Bounding Box Simulation */}
                    <div className="my-auto text-center z-10">
                      <div className="inline-block px-3 py-1 rounded bg-black/70 border border-cyan-400/40 backdrop-blur-sm">
                        <div className="text-[11px] font-bold text-slate-200 truncate max-w-[170px]">
                          {cam.name}
                        </div>
                        <div className="text-[9px] text-slate-400">{cam.zone}</div>
                      </div>
                    </div>

                    {/* Bottom Overlay: Timestamp & Hotlist Alert Status */}
                    <div className="flex items-center justify-between z-10 text-[9px] font-mono text-slate-400">
                      <span>{new Date().toLocaleTimeString()}</span>
                      {hasAlert ? (
                        <span className="text-red-400 font-bold flex items-center gap-1 bg-red-950/80 px-1.5 py-0.5 rounded border border-red-800">
                          <ShieldAlert className="w-3 h-3 text-red-400" /> HOTLIST MATCH
                        </span>
                      ) : (
                        <span className="text-emerald-400">MONITORING NORMAL</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right 1 Col: Live ANPR Detection Stream Ticker */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Car className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Live ANPR Detection Feed
              </h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              {recentDetections.length} Sightings
            </span>
          </div>

          <div className="glass-card p-2.5 max-h-[580px] overflow-y-auto space-y-2">
            {recentDetections.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-xs">
                Waiting for incoming camera events...
              </div>
            ) : (
              recentDetections.map((det) => {
                const isHotlist = ["DL01AB1234", "HR26DQ9988", "UP16AX5544"].includes(det.plate_number);

                return (
                  <div
                    key={det.id || `${det.camera_id}-${det.timestamp}`}
                    className={`p-2.5 rounded-lg border transition-all ${
                      isHotlist
                        ? "bg-red-950/40 border-red-500/60 shadow-sm shadow-red-500/10"
                        : "bg-slate-900/60 border-slate-800 hover:border-cyan-500/40"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      {/* License Plate Badge */}
                      <div className="flex items-center gap-1.5">
                        <div className="px-2 py-0.5 rounded bg-slate-950 border border-slate-700 font-mono font-bold text-xs text-slate-100 tracking-wider">
                          {det.plate_number}
                        </div>
                        {isHotlist && (
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-red-500 text-white animate-pulse">
                            HOTLIST
                          </span>
                        )}
                      </div>

                      {/* Confidence Meter */}
                      <div className="text-right">
                        <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                          {(det.confidence * 100).toFixed(0)}% Conf
                        </span>
                      </div>
                    </div>

                    {/* Sighting Metadata */}
                    <div className="mt-2 grid grid-cols-2 gap-1 text-[11px] text-slate-400">
                      <div className="flex items-center gap-1 truncate">
                        <MapPin className="w-3 h-3 text-cyan-400 shrink-0" />
                        <span className="truncate">{det.camera_name || det.camera_id}</span>
                      </div>
                      <div className="flex items-center gap-1 text-right justify-end">
                        <Clock className="w-3 h-3 text-slate-500 shrink-0" />
                        <span>{new Date(det.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Car className="w-3 h-3 text-slate-500 shrink-0" />
                        <span>{det.vehicle_color || "Dark"} {det.vehicle_type || "Car"}</span>
                      </div>
                      <div className="text-right text-slate-300 font-medium">
                        {det.speed_estimate_kmh?.toFixed(0) || 45} km/h
                      </div>
                    </div>

                    {/* Track Trajectory CTA */}
                    <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-end">
                      <button
                        onClick={() => onSelectPlateForTrajectory(det.plate_number)}
                        className="text-[11px] font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
                      >
                        <span>Reconstruct Path</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
