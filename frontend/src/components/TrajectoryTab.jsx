import React, { useState, useEffect } from "react";
import { 
  Route, 
  Search, 
  Play, 
  Pause, 
  RotateCcw, 
  MapPin, 
  Gauge, 
  Clock, 
  Navigation, 
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Sliders
} from "lucide-react";
import LeafletMap from "./LeafletMap";
import { api } from "../services/api";

export default function TrajectoryTab({
  initialPlate = "DL01AB1234",
  cameras = []
}) {
  const [searchPlate, setSearchPlate] = useState(initialPlate);
  const [trajectory, setTrajectory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // 1x, 2x, 4x

  // Quick select plate options
  const DEMO_PLATES = [
    { plate: "DL01AB1234", label: "Black Scorpio N", type: "CRITICAL ALERT" },
    { plate: "HR26DQ9988", label: "White Creta", type: "STOLEN VEHICLE" },
    { plate: "UP16AX5544", label: "Silver Sedan", type: "REPEAT VIOLATOR" },
    { plate: "DL03CC8899", label: "Civilian Commuter", type: "NORMAL" }
  ];

  const fetchTrajectory = async (plate) => {
    if (!plate) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.queryTrajectory(plate);
      setTrajectory(data);
      setActiveStep(0);
      setIsPlaying(false);
    } catch (err) {
      setError(err.message || "Failed to load trajectory");
      setTrajectory(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialPlate) {
      setSearchPlate(initialPlate);
      fetchTrajectory(initialPlate);
    }
  }, [initialPlate]);

  // Automated Playback Timer
  useEffect(() => {
    let interval = null;
    if (isPlaying && trajectory && trajectory.points.length > 0) {
      interval = setInterval(() => {
        setActiveStep((prev) => {
          if (prev >= trajectory.points.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500 / playbackSpeed);
    }
    return () => clearInterval(interval);
  }, [isPlaying, trajectory, playbackSpeed]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTrajectory(searchPlate);
  };

  const handleQuickPlateSelect = (plate) => {
    setSearchPlate(plate);
    fetchTrajectory(plate);
  };

  const currentPoint = trajectory?.points?.[activeStep];

  return (
    <div className="space-y-4">
      {/* Search & Filter Header */}
      <div className="glass-card p-3.5 flex flex-wrap items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-md">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchPlate}
              onChange={(e) => setSearchPlate(e.target.value.toUpperCase())}
              placeholder="Enter License Plate (e.g. DL01AB1234)..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 font-mono tracking-wider focus:outline-none focus:border-cyan-400"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs rounded-lg transition-all shadow-md shadow-cyan-500/20 disabled:opacity-50"
          >
            {loading ? "Searching..." : "Track Route"}
          </button>
        </form>

        {/* Quick Suggestion Pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-400 font-medium">Quick Demo:</span>
          {DEMO_PLATES.map((item) => (
            <button
              key={item.plate}
              onClick={() => handleQuickPlateSelect(item.plate)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all border ${
                searchPlate === item.plate
                  ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-sm"
                  : "bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700"
              }`}
            >
              <span className="font-bold">{item.plate}</span>
              <span className="text-[9px] text-slate-400 ml-1.5 font-sans">({item.label})</span>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-950/40 border border-red-500/50 rounded-xl text-xs text-red-300 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Content: GIS Map + Trip Telemetry & Timeline */}
      {trajectory && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Left 2 Cols: Leaflet GIS Map & Playback Controls */}
          <div className="lg:col-span-2 space-y-3">
            {/* GIS Interactive Map Canvas */}
            <div className="relative rounded-xl overflow-hidden border border-slate-800 shadow-lg">
              <LeafletMap
                trajectory={trajectory}
                activePlaybackStep={activeStep}
                mode="TRAJECTORY"
                height="500px"
              />

              {/* Floating Active Hop Overlay */}
              {currentPoint && (
                <div className="absolute top-3 left-3 z-[1000] glass-card p-2.5 max-w-xs border border-cyan-400/40 backdrop-blur-md">
                  <div className="flex items-center gap-1.5 text-xs text-cyan-400 font-bold">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>Camera Hop #{activeStep + 1} of {trajectory.points.length}</span>
                  </div>
                  <div className="text-sm font-bold text-slate-100 mt-1">
                    {currentPoint.camera_name}
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                    <span>{new Date(currentPoint.timestamp).toLocaleTimeString()}</span>
                    <span className="text-amber-400">{currentPoint.speed_estimate_kmh} km/h</span>
                  </div>
                </div>
              )}
            </div>

            {/* Playback Control Bar */}
            <div className="glass-card p-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 font-bold hover:scale-105 transition-all shadow-md shadow-cyan-500/20"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-slate-950" />}
                </button>
                <button
                  onClick={() => { setActiveStep(0); setIsPlaying(false); }}
                  className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
                  title="Restart Playback"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>

              {/* Progress Slider */}
              <div className="flex-1 flex items-center gap-3">
                <span className="text-xs font-mono text-cyan-400 font-bold w-12">
                  Hop {activeStep + 1}/{trajectory.points.length}
                </span>
                <input
                  type="range"
                  min={0}
                  max={trajectory.points.length - 1}
                  value={activeStep}
                  onChange={(e) => setActiveStep(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                />
              </div>

              {/* Speed Multiplier */}
              <div className="flex items-center gap-1">
                {[1, 2, 4].map((spd) => (
                  <button
                    key={spd}
                    onClick={() => setPlaybackSpeed(spd)}
                    className={`px-2 py-1 text-xs rounded font-mono font-bold transition-all ${
                      playbackSpeed === spd
                        ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400"
                        : "bg-slate-900 text-slate-400 hover:bg-slate-800"
                    }`}
                  >
                    {spd}x
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right 1 Col: Journey Telemetry & Camera Hop Log */}
          <div className="space-y-3">
            {/* Trip Summary Card */}
            <div className="glass-card p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <div>
                  <div className="text-xs text-slate-400 font-medium">Reconstructed Vehicle</div>
                  <div className="text-xl font-mono font-bold text-cyan-400 tracking-wider">
                    {trajectory.plate_number}
                  </div>
                </div>
                <span className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-xs font-mono text-slate-300">
                  {trajectory.total_sightings} Hits
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase font-medium">Total Distance</div>
                  <div className="text-lg font-bold text-slate-100 font-heading mt-0.5">
                    {trajectory.total_distance_km} km
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase font-medium">Average Velocity</div>
                  <div className="text-lg font-bold text-amber-400 font-heading mt-0.5">
                    {trajectory.average_speed_kmh} km/h
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase font-medium">Origin Zone</div>
                  <div className="text-xs font-bold text-slate-200 mt-0.5 truncate">
                    {trajectory.origin_zone}
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase font-medium">Dest Zone</div>
                  <div className="text-xs font-bold text-slate-200 mt-0.5 truncate">
                    {trajectory.destination_zone}
                  </div>
                </div>
              </div>
            </div>

            {/* Chronological Camera Hops List */}
            <div className="glass-card p-3 space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-300 font-bold uppercase tracking-wider pb-1">
                <span>Waypoint Sightings</span>
                <span className="text-[10px] text-slate-500">Chronological</span>
              </div>

              <div className="max-h-[330px] overflow-y-auto space-y-1.5 pr-1">
                {trajectory.points.map((pt, idx) => {
                  const isCurrent = activeStep === idx;

                  return (
                    <div
                      key={`${pt.camera_id}-${pt.timestamp}`}
                      onClick={() => setActiveStep(idx)}
                      className={`p-2 rounded-lg cursor-pointer transition-all border flex items-center justify-between ${
                        isCurrent
                          ? "bg-cyan-950/40 border-cyan-400 text-cyan-200 shadow-sm"
                          : "bg-slate-900/50 border-slate-800/80 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <div
                          className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                            idx === 0
                              ? "bg-emerald-500 text-slate-950"
                              : idx === trajectory.points.length - 1
                              ? "bg-red-500 text-white"
                              : "bg-cyan-500 text-slate-950"
                          }`}
                        >
                          {idx + 1}
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-200 truncate max-w-[150px]">
                            {pt.camera_name}
                          </div>
                          <div className="text-[10px] text-slate-500 font-mono">
                            {pt.camera_id} • {pt.zone}
                          </div>
                        </div>
                      </div>

                      <div className="text-right text-[11px] font-mono">
                        <div className="text-slate-300">{new Date(pt.timestamp).toLocaleTimeString()}</div>
                        <div className="text-amber-400 text-[10px]">{pt.speed_estimate_kmh} km/h</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
