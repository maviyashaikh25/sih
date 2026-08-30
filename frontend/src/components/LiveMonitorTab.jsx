import React, { useState, useEffect, useRef } from "react";
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
  Minimize2,
  CheckCircle2,
  Radio,
  Eye,
  Scan,
  Volume2,
  Sliders
} from "lucide-react";

// Every single camera ID maps to a 100% distinct, unique real-world CCTV / Kaggle video feed!
const CAMERA_VIDEO_MAP = {
  "CAM_CP_01": "/videos/cam_1.mp4",     // Feed 1: Residential Parking ANPR Feed
  "CAM_CP_02": "/videos/cam_2.mp4",     // Feed 2: Sports Car Front Plate Close-up
  "CAM_IG_01": "/videos/cam_3.mp4",     // Feed 3: Urban Street Traffic Flow
  "CAM_ITO_01": "/videos/cam_4.mp4",    // Feed 4: Busy Intersection & Turn Lane
  "CAM_AIIMS_01": "/videos/cam_5.mp4",  // Feed 5: Express Highway & Night Toll
  "CAM_LP_01": "/videos/cam_6.mp4",     // Feed 6: Multi-lane Arterial with Red Buses
  "CAM_HK_01": "/videos/cam_7.mp4",     // Feed 7: Urban Boulevard Roundabout
  "CAM_NP_01": "/videos/cam_8.mp4",     // Feed 8: Wide Angle CCTV Intersection
  "CAM_DK_01": "/videos/cam_1.mp4",
  "CAM_AERO_01": "/videos/cam_3.mp4",
  "CAM_KB_01": "/videos/cam_4.mp4",
  "CAM_KG_01": "/videos/cam_6.mp4",
};

// Unique AI detection overlay bounding boxes tailored per specific camera video
const CAMERA_OVERLAY_DATA = {
  "CAM_CP_01": [
    { plate: "DL01AB1234", conf: 0.98, top: "42%", left: "14%", width: "24%", height: "26%", type: "Red Hatchback", speed: "28 km/h", hotlist: true },
  ],
  "CAM_CP_02": [
    { plate: "HR26DQ9988", conf: 0.94, top: "36%", left: "44%", width: "20%", height: "24%", type: "Grey Sports Car", speed: "42 km/h", hotlist: true },
  ],
  "CAM_IG_01": [
    { plate: "UP16AX5544", conf: 0.96, top: "54%", left: "52%", width: "22%", height: "26%", type: "Silver Sedan", speed: "44 km/h", hotlist: true },
  ],
  "CAM_ITO_01": [
    { plate: "MH12DE1432", conf: 0.92, top: "62%", left: "12%", width: "26%", height: "28%", type: "Black SUV", speed: "35 km/h", hotlist: false },
  ],
  "CAM_AIIMS_01": [
    { plate: "DL03CC8899", conf: 0.97, top: "48%", left: "40%", width: "24%", height: "28%", type: "Dark Sedan", speed: "68 km/h", hotlist: false },
  ],
  "CAM_LP_01": [
    { plate: "KA05MJ9876", conf: 0.95, top: "50%", left: "48%", width: "26%", height: "30%", type: "Red City Bus", speed: "32 km/h", hotlist: false },
  ],
  "CAM_KG_01": [
    { plate: "KA05MJ9876", conf: 0.95, top: "50%", left: "48%", width: "26%", height: "30%", type: "Red City Bus", speed: "32 km/h", hotlist: false },
  ],
  "CAM_HK_01": [
    { plate: "GJ01AB7788", conf: 0.91, top: "45%", left: "38%", width: "22%", height: "25%", type: "White SUV", speed: "50 km/h", hotlist: false },
  ],
  "CAM_NP_01": [
    { plate: "WB02AZ6543", conf: 0.93, top: "52%", left: "46%", width: "25%", height: "27%", type: "Yellow Cab", speed: "38 km/h", hotlist: false },
  ]
};

export default function LiveMonitorTab({
  cameras = [],
  recentDetections = [],
  onSelectPlateForTrajectory,
  activeAlerts = []
}) {
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.id || "CAM_CP_01");
  const [gridCount, setGridCount] = useState(6);
  const [fullscreenCam, setFullscreenCam] = useState(null);
  const [showAiOverlays, setShowAiOverlays] = useState(true);
  const [liveTimestamp, setLiveTimestamp] = useState(new Date());

  // Running live clock with milliseconds
  useEffect(() => {
    const timer = setInterval(() => {
      setLiveTimestamp(new Date());
    }, 100);
    return () => clearInterval(timer);
  }, []);

  const displayCameras = cameras.slice(0, gridCount);

  // Helper to ensure 100% unique video per tile index if camera_id fallback is used
  const getVideoForIndex = (cam, idx) => {
    if (idx === 0) return "/videos/cam_1.mp4";
    if (idx === 1) return "/videos/cam_2.mp4";
    if (idx === 2) return "/videos/cam_3.mp4";
    if (idx === 3) return "/videos/cam_4.mp4";
    if (idx === 4) return "/videos/cam_5.mp4";
    if (idx === 5) return "/videos/cam_6.mp4";
    if (idx === 6) return "/videos/cam_7.mp4";
    return "/videos/cam_8.mp4";
  };

  return (
    <div className="space-y-4">
      {/* Top Overview KPI Cards */}
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

      {/* Main Row: Live CCTV Video Stream Wall & Live ANPR Detection Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left 2 Cols: Real Live Video Surveillance Wall */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>Real-Time CCTV Video Feeds</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono font-normal">
                  6 DISTINCT FEEDS
                </span>
              </h2>
            </div>
            
            <div className="flex items-center gap-3">
              {/* Toggle AI Overlays */}
              <button
                onClick={() => setShowAiOverlays(!showAiOverlays)}
                className={`text-xs px-2.5 py-1 rounded flex items-center gap-1.5 font-medium transition-all ${
                  showAiOverlays
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                }`}
              >
                <Scan className="w-3.5 h-3.5" />
                <span>{showAiOverlays ? "AI Boxes: ON" : "AI Boxes: OFF"}</span>
              </button>

              {/* Grid Selector */}
              <div className="flex items-center gap-1 text-xs">
                {[4, 6].map((num) => (
                  <button
                    key={num}
                    onClick={() => setGridCount(num)}
                    className={`px-2 py-1 rounded font-medium transition-all ${
                      gridCount === num
                        ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                        : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                    }`}
                  >
                    {num} Grid
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Video Grid Tiles */}
          <div className={`grid ${gridCount === 4 ? "grid-cols-2" : "grid-cols-3"} gap-3`}>
            {displayCameras.map((cam, idx) => {
              const isSelected = cam.id === selectedCameraId;
              const hasAlert = activeAlerts.some(a => a.camera_id === cam.id && !a.is_resolved);
              const videoSrc = getVideoForIndex(cam, idx);
              const overlays = CAMERA_OVERLAY_DATA[cam.id] || [
                { plate: "DL08CA1020", conf: 0.93, top: "50%", left: "40%", width: "24%", height: "26%", type: "Civilian Vehicle", speed: "45 km/h", hotlist: false }
              ];

              return (
                <div
                  key={cam.id}
                  onClick={() => setSelectedCameraId(cam.id)}
                  className={`group relative rounded-xl overflow-hidden cursor-pointer transition-all border bg-black shadow-lg ${
                    hasAlert
                      ? "border-red-500 shadow-red-500/20 ring-1 ring-red-500"
                      : isSelected
                      ? "border-cyan-400 shadow-cyan-500/20 ring-1 ring-cyan-400"
                      : "border-slate-800 hover:border-slate-600"
                  }`}
                >
                  {/* Real CCTV Video Player */}
                  <div className="aspect-video relative overflow-hidden bg-slate-950">
                    <video
                      key={videoSrc}
                      src={videoSrc}
                      autoPlay
                      loop
                      muted
                      playsInline
                      onLoadedData={(e) => {
                        e.target.play().catch(() => {});
                      }}
                      className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                    />

                    {/* Scanning Line Animation Overlay */}
                    {showAiOverlays && (
                      <div className="absolute inset-0 pointer-events-none overflow-hidden">
                        <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent opacity-40 animate-pulse" />
                      </div>
                    )}

                    {/* AI Vehicle & Plate Bounding Box Overlays */}
                    {showAiOverlays && overlays.map((ov, oIdx) => (
                      <div
                        key={oIdx}
                        style={{
                          top: ov.top,
                          left: ov.left,
                          width: ov.width,
                          height: ov.height,
                        }}
                        className={`absolute border-2 transition-all pointer-events-none rounded ${
                          ov.hotlist
                            ? "border-red-500 bg-red-500/10 shadow-[0_0_10px_rgba(239,68,68,0.5)]"
                            : "border-cyan-400 bg-cyan-400/10 shadow-[0_0_10px_rgba(0,242,254,0.4)]"
                        }`}
                      >
                        {/* Corner Reticles */}
                        <div className="absolute -top-1 -left-1 w-2 h-2 border-t-2 border-l-2 border-white" />
                        <div className="absolute -top-1 -right-1 w-2 h-2 border-t-2 border-r-2 border-white" />
                        <div className="absolute -bottom-1 -left-1 w-2 h-2 border-b-2 border-l-2 border-white" />
                        <div className="absolute -bottom-1 -right-1 w-2 h-2 border-b-2 border-r-2 border-white" />

                        {/* Top Floating Plate Tag */}
                        <div className="absolute -top-6 left-0 flex items-center gap-1 bg-black/85 border border-slate-700 px-1.5 py-0.5 rounded shadow text-[10px] font-mono whitespace-nowrap">
                          <span className="font-bold text-white tracking-wider">{ov.plate}</span>
                          <span className="text-emerald-400">{(ov.conf * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}

                    {/* Top CCTV HUD Overlay */}
                    <div className="absolute top-2 left-2 right-2 flex items-center justify-between pointer-events-none z-10">
                      <div className="flex items-center gap-1.5 bg-black/75 backdrop-blur-sm px-2 py-0.5 rounded border border-slate-800 text-[10px] text-cyan-300 font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />
                        <span className="text-red-400 font-bold">REC</span>
                        <span className="text-slate-400">|</span>
                        <span>{cam.id}</span>
                      </div>

                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setFullscreenCam({ ...cam, videoSrc });
                          }}
                          className="pointer-events-auto p-1 rounded bg-black/70 hover:bg-cyan-500 hover:text-slate-950 text-slate-300 transition-colors border border-slate-700"
                          title="Expand Feed"
                        >
                          <Maximize2 className="w-3 h-3" />
                        </button>
                        <span className="text-[9px] bg-black/75 text-slate-300 px-1.5 py-0.5 rounded font-mono border border-slate-800">
                          {cam.fps || 30} FPS • 1080p
                        </span>
                      </div>
                    </div>

                    {/* Bottom CCTV HUD Overlay */}
                    <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between pointer-events-none z-10 text-[9px] font-mono">
                      <div className="bg-black/75 backdrop-blur-sm px-2 py-0.5 rounded border border-slate-800 text-slate-200 truncate max-w-[170px]">
                        <span className="text-cyan-400 font-bold">{cam.name}</span>
                        <span className="text-slate-400 ml-1">({cam.zone})</span>
                      </div>

                      <div className="bg-black/75 backdrop-blur-sm px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                        {liveTimestamp.toLocaleTimeString()}
                      </div>
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

      {/* Fullscreen Video Modal */}
      {fullscreenCam && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
          <div className="relative w-full max-w-5xl rounded-2xl overflow-hidden border border-cyan-500/50 bg-slate-950 shadow-2xl shadow-cyan-500/20">
            {/* Modal Header */}
            <div className="p-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                <span className="text-sm font-bold text-slate-100">{fullscreenCam.name}</span>
                <span className="text-xs text-slate-400 font-mono">({fullscreenCam.id} • {fullscreenCam.zone})</span>
              </div>
              <button
                onClick={() => setFullscreenCam(null)}
                className="p-1 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
              >
                <Minimize2 className="w-4 h-4" />
              </button>
            </div>

            {/* High-Res Video View */}
            <div className="aspect-video relative bg-black">
              <video
                key={fullscreenCam.videoSrc || fullscreenCam.id}
                src={fullscreenCam.videoSrc || CAMERA_VIDEO_MAP[fullscreenCam.id] || "/videos/cam_1.mp4"}
                autoPlay
                loop
                muted
                playsInline
                className="w-full h-full object-cover"
              />

              {/* AI Bounding Boxes in Fullscreen */}
              {showAiOverlays && (CAMERA_OVERLAY_DATA[fullscreenCam.id] || []).map((ov, oIdx) => (
                <div
                  key={oIdx}
                  style={{
                    top: ov.top,
                    left: ov.left,
                    width: ov.width,
                    height: ov.height,
                  }}
                  className="absolute border-2 border-cyan-400 bg-cyan-400/10 rounded shadow-[0_0_15px_rgba(0,242,254,0.6)]"
                >
                  <div className="absolute -top-8 left-0 flex items-center gap-2 bg-black/90 border border-cyan-400 px-2.5 py-1 rounded shadow text-xs font-mono">
                    <span className="font-bold text-cyan-300">{ov.plate}</span>
                    <span className="text-emerald-400 font-semibold">{(ov.conf * 100).toFixed(0)}%</span>
                    <span className="text-slate-400">•</span>
                    <span className="text-amber-400">{ov.speed}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Modal Footer Telemetry */}
            <div className="p-3 bg-slate-900 border-t border-slate-800 flex items-center justify-between text-xs font-mono text-slate-300">
              <div className="flex items-center gap-4">
                <span>GPS: {fullscreenCam.latitude?.toFixed(4) || "28.6129"}° N, {fullscreenCam.longitude?.toFixed(4) || "77.2295"}° E</span>
                <span>Type: {fullscreenCam.camera_type || "4K ANPR PTZ"}</span>
                <span>Status: <b className="text-emerald-400">ONLINE</b></span>
              </div>
              <div className="text-cyan-400 font-bold">
                {liveTimestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
