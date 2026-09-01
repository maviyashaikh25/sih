import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileVideo,
  FileImage,
  CheckCircle2,
  AlertTriangle,
  X,
  Play,
  Loader2,
  Cpu,
  MapPin,
  Car,
  ShieldAlert,
  ArrowRight,
  Sparkles
} from "lucide-react";
import { api } from "../services/api";

export default function UploadFeedModal({
  isOpen,
  onClose,
  cameras = [],
  onFeedProcessed,
  onSelectPlateForTrajectory
}) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  
  // Camera Selection & Configuration
  const [selectedCamId, setSelectedCamId] = useState(cameras[0]?.id || "CAM_CP_01");
  const [isCustomCamera, setIsCustomCamera] = useState(false);
  const [customCamId, setCustomCamId] = useState("");
  const [customCamName, setCustomCamName] = useState("");
  const [customZone, setCustomZone] = useState("Central Corridor");
  const [customLat, setCustomLat] = useState("28.6289");
  const [customLon, setCustomLon] = useState("77.2185");

  // Upload & Inference States
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState("");
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState(null);

  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;
    const ext = selectedFile.name.split(".").pop().toLowerCase();
    const validExtensions = ["mp4", "mov", "avi", "mkv", "webm", "jpg", "jpeg", "png", "webp"];

    if (!validExtensions.includes(ext)) {
      setError(`Invalid file format .${ext}. Supported: MP4, MOV, AVI, MKV, JPG, PNG`);
      return;
    }

    setError(null);
    setResultData(null);
    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleUploadAndRunAI = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a CCTV video clip or camera image to process.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadProgress(15);
    setProcessingStatus("Uploading feed to AI processing node...");

    const formData = new FormData();
    formData.append("file", file);

    const activeCamId = isCustomCamera ? (customCamId || `CAM_UPLOAD_${Date.now().toString().slice(-4)}`) : selectedCamId;
    formData.append("camera_id", activeCamId);

    if (isCustomCamera) {
      formData.append("camera_name", customCamName || `Ingest Point ${activeCamId}`);
      formData.append("zone", customZone);
      formData.append("latitude", customLat);
      formData.append("longitude", customLon);
    }

    try {
      setUploadProgress(45);
      setProcessingStatus("Running YOLOv8 Vehicle Detection & OCR Extraction...");

      const response = await api.uploadCameraFeed(formData);

      setUploadProgress(90);
      setProcessingStatus("Deduplicating plate sightings & generating alerts...");

      setTimeout(() => {
        setUploadProgress(100);
        setIsUploading(false);
        setResultData(response);
        if (onFeedProcessed) {
          onFeedProcessed(response);
        }
      }, 500);

    } catch (err) {
      setIsUploading(false);
      setError(err.message || "Failed to process feed. Please try again.");
    }
  };

  const isVideo = file?.type?.startsWith("video") || ["mp4", "mov", "avi", "webm"].some(ext => file?.name?.toLowerCase().endsWith(ext));

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="relative w-full max-w-3xl rounded-2xl border border-cyan-500/40 bg-slate-950 shadow-2xl shadow-cyan-500/20 overflow-hidden my-8">
        
        {/* Modal Header */}
        <div className="p-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-500/20 border border-cyan-500/50 text-cyan-400">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>Upload Custom CCTV Video / Image Feed</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono">
                  Stage 1: Multi-Camera Ingest
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Process arbitrary CCTV video clips or high-res stills through YOLO vehicle detection & OCR engine
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
          
          {error && (
            <div className="p-3 bg-red-950/40 border border-red-500/50 rounded-xl text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* File Dropzone */}
          {!resultData && (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                isDragOver
                  ? "border-cyan-400 bg-cyan-950/20 scale-[0.99]"
                  : file
                  ? "border-emerald-500/60 bg-slate-900/60"
                  : "border-slate-700 hover:border-cyan-500/50 bg-slate-900/40"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*,image/*,.mp4,.mov,.avi,.jpg,.jpeg,.png"
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files?.[0])}
              />

              {file ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-center gap-3">
                    {isVideo ? (
                      <FileVideo className="w-8 h-8 text-emerald-400 animate-pulse" />
                    ) : (
                      <FileImage className="w-8 h-8 text-emerald-400" />
                    )}
                    <div className="text-left">
                      <div className="text-sm font-bold text-slate-100 font-mono truncate max-w-sm">
                        {file.name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB • {isVideo ? "CCTV Video Stream" : "High-Res Image"}
                      </div>
                    </div>
                  </div>
                  <p className="text-[11px] text-cyan-400 font-medium">
                    Click or drag another file to replace
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center mx-auto text-cyan-400">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-slate-200">
                      Drag and drop CCTV video or image here, or{" "}
                      <span className="text-cyan-400 underline decoration-cyan-400/40">Browse</span>
                    </span>
                    <p className="text-xs text-slate-500 mt-1">
                      Supports MP4, MOV, AVI, JPG, PNG (Max 150MB)
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Camera Node Assignment */}
          {!resultData && (
            <div className="glass-card p-3.5 space-y-3">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                  Assign Camera Node Target
                </span>
                <button
                  type="button"
                  onClick={() => setIsCustomCamera(!isCustomCamera)}
                  className="text-cyan-400 hover:text-cyan-300 text-[11px] font-mono"
                >
                  {isCustomCamera ? "← Select Existing Camera" : "+ Deploy New Custom Camera Node"}
                </button>
              </div>

              {!isCustomCamera ? (
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">Target Camera Node:</label>
                  <select
                    value={selectedCamId}
                    onChange={(e) => setSelectedCamId(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                  >
                    {cameras.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.id} - {c.name} ({c.zone})
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2.5">
                  <div>
                    <label className="text-[10px] text-slate-400">Custom Node ID</label>
                    <input
                      type="text"
                      value={customCamId}
                      onChange={(e) => setCustomCamId(e.target.value.toUpperCase())}
                      placeholder="e.g. CAM_NDLS_01"
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400">Node Name</label>
                    <input
                      type="text"
                      value={customCamName}
                      onChange={(e) => setCustomCamName(e.target.value)}
                      placeholder="e.g. New Delhi Railway Entry"
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400">Zone</label>
                    <input
                      type="text"
                      value={customZone}
                      onChange={(e) => setCustomZone(e.target.value)}
                      placeholder="e.g. Central Delhi"
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
                    />
                  </div>
                  <div className="flex gap-1.5">
                    <div className="w-1/2">
                      <label className="text-[10px] text-slate-400">Latitude</label>
                      <input
                        type="text"
                        value={customLat}
                        onChange={(e) => setCustomLat(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                      />
                    </div>
                    <div className="w-1/2">
                      <label className="text-[10px] text-slate-400">Longitude</label>
                      <input
                        type="text"
                        value={customLon}
                        onChange={(e) => setCustomLon(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload / Inference Progress */}
          {isUploading && (
            <div className="glass-card p-4 space-y-2.5 border border-cyan-500/40 animate-pulse">
              <div className="flex items-center justify-between text-xs text-cyan-300 font-mono">
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                  {processingStatus}
                </span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* AI Inference Results Summary */}
          {resultData && (
            <div className="space-y-4">
              <div className="p-3.5 bg-emerald-950/40 border border-emerald-500/50 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                  <div>
                    <div className="text-xs font-bold text-emerald-300">
                      Feed Processed Successfully!
                    </div>
                    <div className="text-[11px] text-slate-300 font-mono">
                      Camera: <b className="text-white">{resultData.camera_id}</b> ({resultData.camera_name}) • {resultData.detections_count} Vehicle Sightings Extracted
                    </div>
                  </div>
                </div>
                <span className="px-2 py-1 rounded bg-emerald-500/20 text-emerald-300 text-xs font-mono font-bold">
                  {resultData.media_type.toUpperCase()}
                </span>
              </div>

              {/* Detections List */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-300 font-bold uppercase tracking-wider">
                  <span className="flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                    Recognized Number Plates & Telemetry
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {resultData.detections?.length || 0} Detections Ingested
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-56 overflow-y-auto pr-1">
                  {resultData.detections?.map((det, idx) => {
                    const isHotlist = ["DL01AB1234", "HR26DQ9988", "UP16AX5544"].includes(det.plate_number);

                    return (
                      <div
                        key={idx}
                        className={`p-2.5 rounded-lg border transition-all ${
                          isHotlist
                            ? "bg-red-950/40 border-red-500 shadow-sm shadow-red-500/20"
                            : "bg-slate-900/70 border-slate-800"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono font-bold text-xs bg-slate-950 border border-slate-700 px-2 py-0.5 rounded text-white tracking-wider">
                              {det.plate_number}
                            </span>
                            {isHotlist && (
                              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-red-500 text-white">
                                HOTLIST
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                            {(det.confidence * 100).toFixed(0)}% Conf
                          </span>
                        </div>

                        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                          <span className="flex items-center gap-1">
                            <Car className="w-3 h-3 text-cyan-400" />
                            {det.vehicle_color} {det.vehicle_type}
                          </span>
                          <span className="font-mono text-amber-400">
                            {det.speed_estimate_kmh?.toFixed(0)} km/h
                          </span>
                        </div>

                        <div className="mt-2 pt-1.5 border-t border-slate-800/80 flex items-center justify-end">
                          <button
                            onClick={() => {
                              onClose();
                              if (onSelectPlateForTrajectory) {
                                onSelectPlateForTrajectory(det.plate_number);
                              }
                            }}
                            className="text-[10px] font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono"
                          >
                            <span>Trace GIS Trajectory</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-900 border-t border-slate-800 flex items-center justify-between">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs font-semibold transition-colors"
          >
            {resultData ? "Done / Close" : "Cancel"}
          </button>

          {!resultData ? (
            <button
              type="button"
              disabled={!file || isUploading}
              onClick={handleUploadAndRunAI}
              className="px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Cpu className="w-4 h-4" />
                  <span>Ingest & Run ANPR AI</span>
                </>
              )}
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                setFile(null);
                setResultData(null);
                setPreviewUrl(null);
              }}
              className="px-4 py-2 rounded-lg bg-cyan-500/20 border border-cyan-500/50 text-cyan-300 hover:bg-cyan-500/30 text-xs font-semibold transition-all"
            >
              Upload Another Feed
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
