import React, { useState, useEffect, useRef, useMemo } from "react";
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
  Sliders,
  UploadCloud,
  Route,
  Navigation,
  Sparkles,
  Zap,
  Flame,
  Layers
} from "lucide-react";
import UploadFeedModal from "./UploadFeedModal";
import videoTimelineDetections from "../data/videoTimelineDetections.json";

// Default CCTV video feeds per camera node
const CAMERA_VIDEO_MAP = {
  "CAM_KG_01": "/videos/cam_6.mp4",     // Node 1: Kashmere Gate ISBT (Corridor Step 1)
  "CAM_CP_01": "/videos/cam_1.mp4",     // Node 2: Connaught Place (Corridor Step 2)
  "CAM_IG_01": "/videos/cam_3.mp4",     // Node 3: India Gate (Corridor Step 3)
  "CAM_AIIMS_01": "/videos/cam_5.mp4",  // Node 4: AIIMS Flyover (Corridor Step 4)
  "CAM_CP_02": "/videos/cam_2.mp4",
  "CAM_ITO_01": "/videos/cam_4.mp4",
  "CAM_LP_01": "/videos/cam_6.mp4",
  "CAM_HK_01": "/videos/cam_7.mp4",
  "CAM_NP_01": "/videos/cam_8.mp4",
  "CAM_DK_01": "/videos/cam_1.mp4",
  "CAM_AERO_01": "/videos/cam_3.mp4",
  "CAM_KB_01": "/videos/cam_4.mp4",
};

// 4-Node Primary Demonstration Corridor
const CORRIDOR_CAMERA_IDS = ["CAM_KG_01", "CAM_CP_01", "CAM_IG_01", "CAM_AIIMS_01"];

export default function LiveMonitorTab({
  cameras = [],
  recentDetections = [],
  onSelectPlateForTrajectory,
  onNewDetection,
  activeAlerts = [],
  onRefreshCameras
}) {
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.id || "CAM_KG_01");
  const [viewMode, setViewMode] = useState("CORRIDOR"); // 'CORRIDOR' (4 feeds) | 'ALL_GRID' (4 or 6 feeds)
  const [gridCount, setGridCount] = useState(6);
  const [fullscreenCam, setFullscreenCam] = useState(null);
  const [showAiOverlays, setShowAiOverlays] = useState(true);
  const [liveTimestamp, setLiveTimestamp] = useState(new Date());

  // Real-Time Video Playback State for dynamic bounding box interpolation
  // { [camId]: { currentTime: 0, activeBoxes: [] } }
  const [camPlaybackState, setCamPlaybackState] = useState({});
  const videoRefs = useRef({});
  const lastTriggeredEventsRef = useRef({}); // { `${camId}_${plate}_${loopIndex}`: timestamp }

  // Custom Uploaded Feeds Map { cameraId: { url, type: 'video' | 'image', overlayBoxes: [], videoKeyframes: [] } }
  const [customFeedMap, setCustomFeedMap] = useState({});
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Live OCR Search Filter
  const [ocrSearchQuery, setOcrSearchQuery] = useState("");

  // Running live clock
  useEffect(() => {
    const timer = setInterval(() => {
      setLiveTimestamp(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Compute camera list to display based on view mode
  const displayCameras = useMemo(() => {
    if (viewMode === "CORRIDOR") {
      return CORRIDOR_CAMERA_IDS.map(id => 
        cameras.find(c => c.id === id) || { id, name: id, zone: "Corridor Node" }
      );
    }
    return cameras.slice(0, gridCount);
  }, [viewMode, cameras, gridCount]);

  // Handle Video Time Update for Real-Time Detection & Synchronized Bounding Boxes
  const handleTimeUpdate = (camId, currentTime, duration) => {
    const custom = customFeedMap[camId];
    let keyframes = [];

    if (custom?.videoKeyframes && custom.videoKeyframes.length > 0) {
      keyframes = custom.videoKeyframes;
    } else if (videoTimelineDetections[camId]?.keyframes) {
      keyframes = videoTimelineDetections[camId].keyframes;
    }

    if (keyframes.length === 0) return;

    // Find the closest keyframe before or near currentTime
    let activeBoxes = [];
    let closestDiff = Infinity;

    for (const kf of keyframes) {
      const diff = Math.abs(kf.time - (currentTime % (duration || 20)));
      if (diff < closestDiff && diff <= 1.8) {
        closestDiff = diff;
        activeBoxes = kf.boxes || [];
      }
    }

    // Update overlay bounding boxes for this camera
    setCamPlaybackState(prev => ({
      ...prev,
      [camId]: { currentTime, activeBoxes }
    }));

    // Check passing vehicle detection triggers
    const passingEvents = videoTimelineDetections[camId]?.passing_events || [];
    const loopIndex = Math.floor(currentTime / (duration || 20));
    const effectiveTime = currentTime % (duration || 20);

    for (const evt of passingEvents) {
      const timeDiff = Math.abs(evt.trigger_time - effectiveTime);
      if (timeDiff <= 0.8) {
        const triggerKey = `${camId}_${evt.plate_number}_${loopIndex}`;
        const now = Date.now();
        if (!lastTriggeredEventsRef.current[triggerKey] || (now - lastTriggeredEventsRef.current[triggerKey] > 12000)) {
          lastTriggeredEventsRef.current[triggerKey] = now;

          if (onNewDetection) {
            const newDetObj = {
              id: `${camId}-${evt.plate_number}-${Date.now()}`,
              camera_id: camId,
              camera_name: evt.camera_name,
              zone: evt.zone,
              plate_number: evt.plate_number,
              confidence: evt.confidence,
              vehicle_type: evt.vehicle_type,
              vehicle_color: evt.vehicle_color,
              speed_estimate_kmh: evt.speed_estimate_kmh,
              direction: evt.direction || "Inbound Flow",
              hotlist: evt.hotlist || ["KA02MN1826", "DL01AB1234", "HR26DQ9988", "UP16AX5544"].includes(evt.plate_number),
              timestamp: new Date().toISOString()
            };
            onNewDetection(newDetObj);
          }
        }
      }
    }
  };

  const handleFeedUploadComplete = (uploadResponse) => {
    if (uploadResponse?.camera_id && uploadResponse?.feed_url) {
      setCustomFeedMap(prev => ({
        ...prev,
        [uploadResponse.camera_id]: {
          url: `http://127.0.0.1:8000${uploadResponse.feed_url}`,
          type: uploadResponse.media_type,
          overlayBoxes: uploadResponse.overlay_boxes || [],
          videoKeyframes: uploadResponse.video_keyframes || []
        }
      }));
      setSelectedCameraId(uploadResponse.camera_id);

      // Prepend all detections from uploaded feed to live detection list
      if (uploadResponse.detections && uploadResponse.detections.length > 0) {
        uploadResponse.detections.forEach(d => {
          if (onNewDetection) {
            onNewDetection({
              ...d,
              timestamp: d.timestamp || new Date().toISOString(),
              hotlist: d.hotlist || ["KA02MN1826", "DL01AB1234", "HR26DQ9988"].includes(d.plate_number)
            });
          }
        });
      }
    }
    if (onRefreshCameras) {
      onRefreshCameras();
    }
  };

  // Filter recent detections by plate query
  const filteredDetections = useMemo(() => {
    if (!ocrSearchQuery.trim()) return recentDetections;
    return recentDetections.filter(d => 
      d.plate_number?.toUpperCase().includes(ocrSearchQuery.toUpperCase().trim()) ||
      d.camera_name?.toLowerCase().includes(ocrSearchQuery.toLowerCase().trim()) ||
      d.camera_id?.toLowerCase().includes(ocrSearchQuery.toLowerCase().trim())
    );
  }, [recentDetections, ocrSearchQuery]);

  return (
    <div className="space-y-4">
      {/* Upload Feed Modal */}
      <UploadFeedModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        cameras={cameras}
        onFeedProcessed={handleFeedUploadComplete}
        onSelectPlateForTrajectory={onSelectPlateForTrajectory}
      />

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
            <span>Active Camera Nodes</span>
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
            <span>Corridor Avg Speed</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100 font-heading">49.2 km/h</span>
            <span className="text-xs text-slate-400">Optimal Flow</span>
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

      {/* Corridor Demonstration Pathway Banner */}
      {viewMode === "CORRIDOR" && (
        <div className="glass-card p-3 border border-cyan-500/40 bg-gradient-to-r from-cyan-950/40 via-slate-900/60 to-blue-950/40 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
              <Route className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-cyan-300 flex items-center gap-2">
                <span>4-NODE CROSS-CITY CORRIDOR DEMONSTRATION</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-red-500 text-white font-mono animate-pulse">
                  TARGET: DL01AB1234
                </span>
              </div>
              <div className="text-[11px] text-slate-300 font-mono mt-0.5 flex items-center gap-1.5 flex-wrap">
                <span className="text-emerald-400 font-bold">1. Kashmere Gate ISBT</span>
                <ArrowRight className="w-3 h-3 text-cyan-400" />
                <span className="text-slate-200">2. Connaught Place Radial</span>
                <ArrowRight className="w-3 h-3 text-cyan-400" />
                <span className="text-slate-200">3. India Gate Hexagon</span>
                <ArrowRight className="w-3 h-3 text-cyan-400" />
                <span className="text-amber-400 font-bold">4. AIIMS Flyover</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onSelectPlateForTrajectory("DL01AB1234")}
            className="px-3.5 py-1.5 bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white text-xs font-bold rounded-lg transition-all shadow-md shadow-red-500/20 flex items-center gap-1.5"
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>Trace Corridor GIS Route</span>
          </button>
        </div>
      )}

      {/* Main Row: Live CCTV Video Stream Wall & Live ANPR Detection Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
        {/* Left 2 Cols: Real Live Video Surveillance Wall */}
        <div className="lg:col-span-2 space-y-3">
          
          {/* Surveillance Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2.5">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
              </span>
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <span>{viewMode === "CORRIDOR" ? "4-Feed Corridor Pipeline" : "Real-Time CCTV Video Feeds"}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono font-normal">
                  {displayCameras.length} STREAMS LIVE
                </span>
              </h2>
            </div>
            
            <div className="flex items-center gap-2 flex-wrap">
              {/* Upload Custom Feed Button */}
              <button
                onClick={() => setIsUploadModalOpen(true)}
                className="text-xs px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold transition-all shadow-md shadow-cyan-500/20 flex items-center gap-1.5"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                <span>Upload Feed</span>
              </button>

              {/* View Mode Toggle: Corridor vs Full Grid */}
              <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs">
                <button
                  onClick={() => setViewMode("CORRIDOR")}
                  className={`px-2.5 py-1 rounded font-medium transition-all ${
                    viewMode === "CORRIDOR"
                      ? "bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  4-Feed Corridor
                </button>
                <button
                  onClick={() => setViewMode("ALL_GRID")}
                  className={`px-2.5 py-1 rounded font-medium transition-all ${
                    viewMode === "ALL_GRID"
                      ? "bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  All Cameras ({gridCount})
                </button>
              </div>

              {/* Toggle AI Overlays */}
              <button
                onClick={() => setShowAiOverlays(!showAiOverlays)}
                className={`text-xs px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 font-medium transition-all ${
                  showAiOverlays
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                }`}
              >
                <Scan className="w-3.5 h-3.5" />
                <span>{showAiOverlays ? "AI HUD: ON" : "AI HUD: OFF"}</span>
              </button>

              {/* Grid Selector for ALL_GRID view */}
              {viewMode === "ALL_GRID" && (
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
                      {num}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Video Grid Tiles */}
          <div className={`grid ${viewMode === "CORRIDOR" || gridCount === 4 ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"} gap-3`}>
            {displayCameras.map((cam, idx) => {
              const isSelected = cam.id === selectedCameraId;
              const hasAlert = activeAlerts.some(a => a.camera_id === cam.id && !a.is_resolved);
              
              const customFeed = customFeedMap[cam.id];
              const isCustomImage = customFeed?.type === "image";
              const mediaSrc = customFeed?.url || CAMERA_VIDEO_MAP[cam.id] || `/videos/cam_${(idx % 8) + 1}.mp4`;
              
              // Dynamic live vehicle bounding boxes from active playback or custom upload
              let activeOverlays = [];
              if (isCustomImage && customFeed?.overlayBoxes?.length > 0) {
                activeOverlays = customFeed.overlayBoxes;
              } else if (camPlaybackState[cam.id]?.activeBoxes?.length > 0) {
                activeOverlays = camPlaybackState[cam.id].activeBoxes;
              } else if (videoTimelineDetections[cam.id]?.keyframes?.[0]?.boxes) {
                activeOverlays = videoTimelineDetections[cam.id].keyframes[0].boxes;
              }

              const corridorStepLabels = [
                { num: "01", stage: "ORIGIN", road: "Kashmere Gate ISBT" },
                { num: "02", stage: "TRANSIT", road: "Connaught Place Radial" },
                { num: "03", stage: "TRANSIT", road: "India Gate Hexagon" },
                { num: "04", stage: "INTERCEPT", road: "AIIMS Ring Road" },
              ];
              const stepInfo = viewMode === "CORRIDOR" ? corridorStepLabels[idx] : null;

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
                  {/* Real CCTV Video or Uploaded Image Player */}
                  <div className="aspect-video relative overflow-hidden bg-slate-950">
                    {isCustomImage ? (
                      <img
                        src={mediaSrc}
                        alt={`Camera ${cam.id}`}
                        className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                      />
                    ) : (
                      <video
                        ref={el => { videoRefs.current[cam.id] = el; }}
                        key={mediaSrc}
                        src={mediaSrc}
                        autoPlay
                        loop
                        muted
                        playsInline
                        onTimeUpdate={(e) => {
                          handleTimeUpdate(cam.id, e.target.currentTime, e.target.duration);
                        }}
                        onLoadedData={(e) => {
                          e.target.play().catch(() => {});
                        }}
                        className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                      />
                    )}

                    {/* Scanning Line Animation Overlay */}
                    {showAiOverlays && (
                      <div className="absolute inset-0 pointer-events-none overflow-hidden">
                        <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent opacity-40 animate-pulse" />
                      </div>
                    )}

                    {/* AI Vehicle & Plate Bounding Box Overlays (Synchronized in Real-Time) */}
                    {showAiOverlays && activeOverlays.map((ov, oIdx) => (
                      <div
                        key={`${ov.plate}-${oIdx}`}
                        style={{
                          top: ov.top,
                          left: ov.left,
                          width: ov.width,
                          height: ov.height,
                        }}
                        className={`absolute border-2 transition-all duration-300 pointer-events-none rounded ${
                          ov.hotlist
                            ? "border-red-500 bg-red-500/15 shadow-[0_0_15px_rgba(239,68,68,0.7)] animate-pulse"
                            : "border-cyan-400 bg-cyan-400/10 shadow-[0_0_10px_rgba(0,242,254,0.4)]"
                        }`}
                      >
                        {/* Corner Reticles */}
                        <div className="absolute -top-1 -left-1 w-2 h-2 border-t-2 border-l-2 border-white" />
                        <div className="absolute -top-1 -right-1 w-2 h-2 border-t-2 border-r-2 border-white" />
                        <div className="absolute -bottom-1 -left-1 w-2 h-2 border-b-2 border-l-2 border-white" />
                        <div className="absolute -bottom-1 -right-1 w-2 h-2 border-b-2 border-r-2 border-white" />

                        {/* Top Floating Plate Tag */}
                        <div className="absolute -top-6 left-0 flex items-center gap-1 bg-black/90 border border-slate-700 px-1.5 py-0.5 rounded shadow text-[10px] font-mono whitespace-nowrap z-20">
                          <span className={`font-bold tracking-wider ${ov.hotlist ? "text-red-400 animate-pulse" : "text-white"}`}>
                            {ov.plate}
                          </span>
                          <span className="text-emerald-400">{(ov.conf * 100).toFixed(0)}%</span>
                        </div>

                        {/* Bottom Vehicle Type & Speed Tag */}
                        <div className="absolute -bottom-5 left-0 flex items-center gap-1 bg-black/80 px-1 py-0.2 rounded text-[9px] font-mono text-slate-300 whitespace-nowrap">
                          <span>{ov.type || "Vehicle"}</span>
                          <span className="text-cyan-400">• {ov.speed || "45 km/h"}</span>
                        </div>
                      </div>
                    ))}

                    {/* Top CCTV HUD Overlay */}
                    <div className="absolute top-2 left-2 right-2 flex items-center justify-between pointer-events-none z-10">
                      <div className="flex items-center gap-1.5 bg-black/80 backdrop-blur-sm px-2 py-0.5 rounded border border-slate-800 text-[10px] text-cyan-300 font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />
                        <span className="text-red-400 font-bold">LIVE</span>
                        <span className="text-slate-400">|</span>
                        <span>{cam.id}</span>
                        {customFeed && (
                          <span className="text-[9px] px-1 bg-cyan-500/30 text-cyan-200 rounded font-sans">
                            UPLOADED
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-1">
                        {stepInfo && (
                          <span className="text-[9px] bg-cyan-950/90 text-cyan-300 px-1.5 py-0.5 rounded font-mono font-bold border border-cyan-500/50">
                            STEP {stepInfo.num}: {stepInfo.stage}
                          </span>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setFullscreenCam({ ...cam, mediaSrc, isCustomImage, activeOverlays });
                          }}
                          className="pointer-events-auto p-1 rounded bg-black/70 hover:bg-cyan-500 hover:text-slate-950 text-slate-300 transition-colors border border-slate-700"
                          title="Expand Feed"
                        >
                          <Maximize2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>

                    {/* Bottom CCTV HUD Overlay */}
                    <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between pointer-events-none z-10 text-[9px] font-mono">
                      <div className="bg-black/80 backdrop-blur-sm px-2 py-0.5 rounded border border-slate-800 text-slate-200 truncate max-w-[200px]">
                        <span className="text-cyan-400 font-bold">{cam.name}</span>
                        <span className="text-slate-400 ml-1">({cam.zone})</span>
                      </div>

                      <div className="bg-black/80 backdrop-blur-sm px-2 py-0.5 rounded border border-slate-800 text-slate-300">
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
          
          {/* Ticker Header & Search */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Car className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <span>Live OCR Detection Feed</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                </h2>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                {filteredDetections.length} Sightings
              </span>
            </div>

            {/* Instant Filter */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={ocrSearchQuery}
                onChange={(e) => setOcrSearchQuery(e.target.value)}
                placeholder="Filter plate (e.g. DL01, HR26, UP07)..."
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          {/* Detections Stream List */}
          <div className="glass-card p-2.5 max-h-[580px] overflow-y-auto space-y-2">
            {filteredDetections.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-xs">
                No plate sightings match the filter. Waiting for passing vehicles in live feeds...
              </div>
            ) : (
              filteredDetections.map((det, dIdx) => {
                const isHotlist = det.hotlist || ["KA02MN1826", "DL01AB1234", "HR26DQ9988", "UP16AX5544"].includes(det.plate_number);
                const isRecent = dIdx < 2;

                return (
                  <div
                    key={`det-${det.id ?? ''}-${det.camera_id ?? ''}-${det.plate_number ?? ''}-${det.timestamp ?? ''}-${dIdx}`}
                    className={`p-2.5 rounded-lg border transition-all ${
                      isHotlist
                        ? "bg-red-950/40 border-red-500/60 shadow-sm shadow-red-500/20 ring-1 ring-red-500/50"
                        : isRecent
                        ? "bg-slate-900/90 border-cyan-500/50 shadow-sm shadow-cyan-500/10"
                        : "bg-slate-900/60 border-slate-800 hover:border-cyan-500/40"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      {/* License Plate Badge */}
                      <div className="flex items-center gap-1.5">
                        <div className={`px-2 py-0.5 rounded border font-mono font-bold text-xs tracking-wider ${
                          isHotlist
                            ? "bg-red-900/40 border-red-500 text-red-200"
                            : "bg-slate-950 border-slate-700 text-slate-100"
                        }`}>
                          {det.plate_number}
                        </div>
                        {isHotlist && (
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-red-500 text-white animate-pulse flex items-center gap-0.5">
                            <Flame className="w-2.5 h-2.5" />
                            <span>HOTLIST</span>
                          </span>
                        )}
                        {isRecent && !isHotlist && (
                          <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 font-mono animate-pulse">
                            NEW
                          </span>
                        )}
                      </div>

                      {/* Confidence Meter */}
                      <div className="text-right">
                        <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                          {((det.confidence || 0.95) * 100).toFixed(0)}% Conf
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
                        <span>{det.vehicle_color || ""} {det.vehicle_type || "Vehicle"}</span>
                      </div>
                      <div className="text-right text-slate-300 font-medium">
                        {det.speed_estimate_kmh?.toFixed ? det.speed_estimate_kmh.toFixed(0) : det.speed_estimate_kmh || 45} km/h
                      </div>
                    </div>

                    {/* Track Trajectory CTA */}
                    <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-end">
                      <button
                        onClick={() => onSelectPlateForTrajectory(det.plate_number)}
                        className="text-[11px] font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors font-mono"
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

            {/* High-Res Media View */}
            <div className="aspect-video relative bg-black">
              {fullscreenCam.isCustomImage ? (
                <img
                  src={fullscreenCam.mediaSrc}
                  alt={fullscreenCam.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <video
                  key={fullscreenCam.mediaSrc || fullscreenCam.id}
                  src={fullscreenCam.mediaSrc || CAMERA_VIDEO_MAP[fullscreenCam.id] || "/videos/cam_1.mp4"}
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="w-full h-full object-cover"
                />
              )}

              {/* AI Bounding Boxes in Fullscreen */}
              {showAiOverlays && (camPlaybackState[fullscreenCam.id]?.activeBoxes || fullscreenCam.activeOverlays || []).map((ov, oIdx) => (
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
                <span>GPS: {fullscreenCam.latitude?.toFixed ? fullscreenCam.latitude.toFixed(4) : "28.6129"}° N, {fullscreenCam.longitude?.toFixed ? fullscreenCam.longitude.toFixed(4) : "77.2295"}° E</span>
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
