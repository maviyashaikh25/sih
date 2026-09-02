import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { 
  Compass, 
  Maximize2, 
  Minimize2, 
  Crosshair, 
  Radio, 
  Activity,
  Satellite,
  Map as MapIcon,
  Globe,
  Layers
} from "lucide-react";

// Real-World Map Tile Providers
const TILE_PROVIDERS = {
  satellite_hybrid: {
    name: "Google Satellite Hybrid",
    shortName: "Satellite",
    badge: "REAL AERIAL",
    url: "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    attribution: "&copy; Google Maps Real Satellite",
    maxZoom: 20,
    subdomains: []
  },
  google_streets: {
    name: "Google Real Streets",
    shortName: "Google Roads",
    badge: "MAP",
    url: "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attribution: "&copy; Google Maps Vector",
    maxZoom: 20,
    subdomains: []
  },
  carto_voyager: {
    name: "OpenStreetMap India (Voyager)",
    shortName: "OSM India",
    badge: "OPEN MAP",
    url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
    maxZoom: 19,
    subdomains: ["a", "b", "c", "d"]
  },
  google_traffic: {
    name: "Live Traffic Grid",
    shortName: "Live Traffic",
    badge: "TRAFFIC",
    url: "https://mt1.google.com/vt/lyrs=m,traffic&x={x}&y={y}&z={z}",
    attribution: "&copy; Google Live Traffic",
    maxZoom: 20,
    subdomains: []
  },
  esri_satellite: {
    name: "Esri World Imagery",
    shortName: "Esri Aerial",
    badge: "HD PHOTO",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "&copy; Esri World Imagery",
    maxZoom: 19,
    subdomains: []
  },
  carto_dark: {
    name: "Tactical Night Radar",
    shortName: "Tactical Dark",
    badge: "NIGHT",
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> Dark Matter',
    maxZoom: 19,
    subdomains: ["a", "b", "c", "d"]
  }
};

export default function LeafletMap({
  cameras = [],
  trajectory = null,
  activePlaybackStep = null,
  heatmapPoints = [],
  center = [28.6139, 77.2090], // Default New Delhi center
  zoom = 13,
  mode = "TRAJECTORY", // 'TRAJECTORY', 'HEATMAP', 'CAMERAS'
  onCameraClick = null,
  height = "520px"
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const currentTileLayerRef = useRef(null);
  const layerGroupRef = useRef(null);
  const wrapperRef = useRef(null);

  const [activeTileKey, setActiveTileKey] = useState("satellite_hybrid");
  const [cursorCoords, setCursorCoords] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentZoom, setCurrentZoom] = useState(zoom);

  // 1. Initialize Leaflet Map instance
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: center,
        zoom: zoom,
        zoomControl: false,
        attributionControl: true
      });

      L.control.zoom({ position: "bottomright" }).addTo(map);

      // Add default tile layer (Google Satellite Hybrid for crisp photorealism)
      const provider = TILE_PROVIDERS[activeTileKey] || TILE_PROVIDERS.satellite_hybrid;
      const tileLayer = L.tileLayer(provider.url, {
        attribution: provider.attribution,
        maxZoom: provider.maxZoom || 19,
        subdomains: provider.subdomains || []
      }).addTo(map);

      currentTileLayerRef.current = tileLayer;

      const layerGroup = L.layerGroup().addTo(map);
      layerGroupRef.current = layerGroup;
      mapInstanceRef.current = map;

      // Event listeners
      map.on("mousemove", (e) => {
        setCursorCoords({
          lat: e.latlng.lat.toFixed(5),
          lng: e.latlng.lng.toFixed(5)
        });
      });

      map.on("zoomend", () => {
        setCurrentZoom(map.getZoom());
      });
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // 2. Change Tile Layer when user switches style
  const handleLayerChange = (key) => {
    setActiveTileKey(key);
    const map = mapInstanceRef.current;
    if (!map) return;

    if (currentTileLayerRef.current) {
      try {
        map.removeLayer(currentTileLayerRef.current);
      } catch (e) {
        console.warn("Error removing layer:", e);
      }
    }

    const provider = TILE_PROVIDERS[key] || TILE_PROVIDERS.satellite_hybrid;
    const newTileLayer = L.tileLayer(provider.url, {
      attribution: provider.attribution,
      maxZoom: provider.maxZoom || 19,
      subdomains: provider.subdomains || []
    }).addTo(map);

    currentTileLayerRef.current = newTileLayer;
    newTileLayer.bringToBack();
  };

  // Recenter map helper
  const handleRecenter = () => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (mode === "TRAJECTORY" && trajectory?.points?.length > 0) {
      const latLngs = trajectory.points.map(p => [p.latitude, p.longitude]);
      map.fitBounds(latLngs, { padding: [50, 50] });
    } else if (cameras?.length > 0) {
      const latLngs = cameras.map(c => [c.latitude, c.longitude]);
      map.fitBounds(latLngs, { padding: [50, 50] });
    } else {
      map.setView(center, zoom);
    }
  };

  // Toggle Fullscreen
  const toggleFullscreen = () => {
    if (!wrapperRef.current) return;
    if (!document.fullscreenElement) {
      wrapperRef.current.requestFullscreen().catch((err) => {
        console.warn("Error attempting to enable fullscreen:", err);
      });
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // 3. Render dynamic spatial overlays (Trajectories, Heatmap, Cameras)
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();

    // --- MODE 1: TRAJECTORY PLAYBACK ---
    if (mode === "TRAJECTORY" && trajectory && trajectory.points && trajectory.points.length > 0) {
      const points = trajectory.points;
      const latLngs = points.map(p => [p.latitude, p.longitude]);

      // Draw route path
      // 1. Glowing outer halo
      L.polyline(latLngs, {
        color: "#00f2fe",
        weight: 6,
        opacity: 0.85,
        lineCap: "round",
        lineJoin: "round"
      }).addTo(layerGroup);

      // 2. Inner dashed neon corridor line
      L.polyline(latLngs, {
        color: "#ffffff",
        weight: 2.5,
        opacity: 0.95,
        dashArray: "6, 8"
      }).addTo(layerGroup);

      // Draw numbered camera pins along trajectory
      // If there are many points, highlight start, end, active step, and key hops
      points.forEach((pt, idx) => {
        const isStart = idx === 0;
        const isEnd = idx === points.length - 1;
        const isCurrent = activePlaybackStep === idx;

        const pinColor = isStart ? "#10b981" : (isEnd ? "#ef4444" : (isCurrent ? "#f59e0b" : "#0284c7"));
        const statusLabel = isStart ? "ORIGIN" : (isEnd ? "LAST SEEN" : `WAYPOINT #${idx + 1}`);

        const pinHtml = `
          <div style="
            background: radial-gradient(circle, ${pinColor} 0%, #0f172a 100%);
            color: #ffffff;
            font-weight: 800;
            font-size: 11px;
            width: ${isCurrent ? '34px' : '28px'};
            height: ${isCurrent ? '34px' : '28px'};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2.5px solid ${isCurrent ? '#fbbf24' : '#ffffff'};
            box-shadow: 0 0 14px ${pinColor}, 0 4px 8px rgba(0,0,0,0.8);
            transform: translate(-50%, -50%);
            transition: all 0.2s ease;
          ">
            ${idx + 1}
          </div>
        `;

        const customIcon = L.divIcon({
          html: pinHtml,
          className: "trajectory-waypoint",
          iconSize: [30, 30]
        });

        const marker = L.marker([pt.latitude, pt.longitude], { icon: customIcon }).addTo(layerGroup);
        marker.bindPopup(`
          <div style="font-family: system-ui, -apple-system, sans-serif; min-width: 220px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
              <span style="background: ${pinColor}; color: #000; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px;">
                ${statusLabel}
              </span>
              <span style="color: #38bdf8; font-size: 11px; font-weight: 700;">${pt.camera_id}</span>
            </div>
            <div style="color: #f8fafc; font-weight: 700; font-size: 13px; margin-bottom: 4px;">
              ${pt.camera_name}
            </div>
            <div style="background: rgba(15, 23, 42, 0.85); border-radius: 6px; padding: 6px 8px; font-size: 11px; border: 1px solid rgba(56, 189, 248, 0.25);">
              <div style="color: #94a3b8; display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span>Zone:</span>
                <b style="color: #e2e8f0;">${pt.zone}</b>
              </div>
              <div style="color: #94a3b8; display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span>Timestamp:</span>
                <b style="color: #00f2fe;">${new Date(pt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</b>
              </div>
              <div style="color: #94a3b8; display: flex; justify-content: space-between;">
                <span>Est. Speed:</span>
                <b style="color: #fbbf24;">${pt.speed_estimate_kmh} km/h</b>
              </div>
            </div>
          </div>
        `);
      });

      // Draw current playback vehicle indicator if step selected
      if (activePlaybackStep !== null && points[activePlaybackStep]) {
        const curPt = points[activePlaybackStep];
        const vehHtml = `
          <div style="
            position: relative;
            transform: translate(-50%, -50%);
          ">
            <div style="
              position: absolute;
              top: -8px;
              left: -8px;
              width: 52px;
              height: 52px;
              border-radius: 50%;
              border: 2px solid #f59e0b;
              animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
              opacity: 0.85;
            "></div>
            <div style="
              background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
              color: #000;
              width: 38px;
              height: 38px;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              border: 3px solid #ffffff;
              box-shadow: 0 0 20px #f59e0b, 0 6px 14px rgba(0,0,0,0.8);
              font-size: 17px;
            ">
              🚗
            </div>
          </div>
        `;
        const vehIcon = L.divIcon({
          html: vehHtml,
          className: "active-vehicle-marker",
          iconSize: [38, 38]
        });
        L.marker([curPt.latitude, curPt.longitude], { icon: vehIcon, zIndexOffset: 1000 }).addTo(layerGroup);
      }

      // Auto-fit bounds
      map.fitBounds(latLngs, { padding: [50, 50] });
    }

    // --- MODE 2: MACRO HEATMAP ---
    else if (mode === "HEATMAP" && heatmapPoints && heatmapPoints.length > 0) {
      heatmapPoints.forEach(hp => {
        let circleColor = "#10b981"; // Low (Green)
        if (hp.congestion_level === "CRITICAL") circleColor = "#ef4444"; // Red
        else if (hp.congestion_level === "HIGH") circleColor = "#f97316"; // Orange
        else if (hp.congestion_level === "MEDIUM") circleColor = "#eab308"; // Yellow

        const radius = Math.max(350, hp.vehicle_count * 50);

        const circle = L.circle([hp.latitude, hp.longitude], {
          color: circleColor,
          fillColor: circleColor,
          fillOpacity: 0.45 + (hp.intensity * 0.35),
          weight: 2.5,
          radius: radius
        }).addTo(layerGroup);

        circle.bindPopup(`
          <div style="font-family: system-ui, -apple-system, sans-serif; min-width: 200px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
              <span style="color: ${circleColor}; font-weight: 800; font-size: 12px;">${hp.camera_name}</span>
              <span style="background: ${circleColor}22; color: ${circleColor}; border: 1px solid ${circleColor}; font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 4px;">
                ${hp.congestion_level}
              </span>
            </div>
            <div style="background: rgba(15, 23, 42, 0.85); border-radius: 6px; padding: 6px 8px; font-size: 11px; margin-top: 6px; border: 1px solid rgba(56, 189, 248, 0.25);">
              <div style="color: #cbd5e1; display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span>Rolling Count:</span>
                <b style="color: #ffffff;">${hp.vehicle_count} vehicles</b>
              </div>
              <div style="color: #94a3b8; display: flex; justify-content: space-between;">
                <span>Density Index:</span>
                <b style="color: ${circleColor};">${(hp.intensity * 100).toFixed(0)}%</b>
              </div>
            </div>
          </div>
        `);
      });
    }

    // --- MODE 3: DEFAULT CAMERAS GRID ---
    else if (cameras && cameras.length > 0) {
      cameras.forEach(cam => {
        const camHtml = `
          <div style="
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #00f2fe;
            border: 2px solid #00f2fe;
            font-size: 13px;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.6), 0 4px 8px rgba(0,0,0,0.7);
            transform: translate(-50%, -50%);
            cursor: pointer;
            transition: all 0.2s ease;
          ">
            📷
          </div>
        `;

        const camIcon = L.divIcon({
          html: camHtml,
          className: "camera-pin",
          iconSize: [32, 32]
        });

        const marker = L.marker([cam.latitude, cam.longitude], { icon: camIcon }).addTo(layerGroup);
        marker.bindPopup(`
          <div style="font-family: system-ui, -apple-system, sans-serif; min-width: 210px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
              <span style="color: #00f2fe; font-weight: 800; font-size: 12px;">${cam.id}</span>
              <span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981; font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 4px;">
                ● ${cam.fps || 30} FPS LIVE
              </span>
            </div>
            <div style="color: #f8fafc; font-weight: 700; font-size: 13px; margin-bottom: 4px;">${cam.name}</div>
            <div style="background: rgba(15, 23, 42, 0.85); border-radius: 6px; padding: 6px 8px; font-size: 11px; border: 1px solid rgba(56, 189, 248, 0.25);">
              <div style="color: #94a3b8; display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span>Zone:</span>
                <b style="color: #e2e8f0;">${cam.zone}</b>
              </div>
              <div style="color: #94a3b8; display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span>Corridor:</span>
                <b style="color: #38bdf8;">${cam.road_name || 'Metropolitan Expressway'}</b>
              </div>
              <div style="color: #94a3b8; display: flex; justify-content: space-between;">
                <span>Coordinates:</span>
                <b style="color: #cbd5e1;">${cam.latitude.toFixed(4)}, ${cam.longitude.toFixed(4)}</b>
              </div>
            </div>
          </div>
        `);

        if (onCameraClick) {
          marker.on("click", () => onCameraClick(cam));
        }
      });
    }
  }, [cameras, trajectory, activePlaybackStep, heatmapPoints, mode]);

  return (
    <div 
      ref={wrapperRef}
      className="relative w-full rounded-xl overflow-hidden border border-cyan-500/20 shadow-2xl bg-slate-950"
      style={{ height: height }}
    >
      {/* Map Container */}
      <div
        ref={mapContainerRef}
        style={{ width: "100%", height: "100%", background: "#0f172a" }}
      />

      {/* Floating Layer Switcher Pill (Top Right) */}
      <div className="absolute top-3 right-3 z-[1000] flex items-center gap-1.5 bg-slate-950/90 backdrop-blur-md p-1 rounded-xl border border-cyan-500/30 shadow-2xl max-w-[calc(100%-140px)] overflow-x-auto">
        {Object.entries(TILE_PROVIDERS).map(([key, provider]) => {
          const isActive = activeTileKey === key;
          return (
            <button
              key={key}
              onClick={() => handleLayerChange(key)}
              title={provider.name}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 shrink-0 ${
                isActive
                  ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 shadow-md shadow-cyan-500/30 font-bold"
                  : "text-slate-300 hover:text-white hover:bg-slate-800/80"
              }`}
            >
              <span>{provider.shortName}</span>
              {provider.badge && (
                <span className={`text-[8px] px-1 py-0.2 rounded font-mono font-bold ${
                  isActive ? "bg-slate-950 text-cyan-300" : "bg-cyan-950 text-cyan-400 border border-cyan-800"
                }`}>
                  {provider.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Floating HUD Tools (Top Left) */}
      <div className="absolute top-3 left-3 z-[1000] flex items-center gap-2">
        <button
          onClick={handleRecenter}
          title="Recenter & Fit View"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-950/90 backdrop-blur-md border border-cyan-500/30 rounded-lg text-xs font-semibold text-cyan-400 hover:text-cyan-300 hover:bg-slate-900 transition-all shadow-lg"
        >
          <Crosshair className="w-3.5 h-3.5" />
          <span>Fit View</span>
        </button>

        <button
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Map"}
          className="p-1.5 bg-slate-950/90 backdrop-blur-md border border-slate-800 rounded-lg text-slate-300 hover:text-white hover:bg-slate-900 transition-all shadow-lg"
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* Live Telemetry & GPS Coordinates Bar (Bottom Left) */}
      <div className="absolute bottom-3 left-3 z-[1000] flex items-center gap-2 bg-slate-950/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-400 shadow-xl pointer-events-none">
        <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          <span>GIS:</span>
        </div>
        <span>
          {cursorCoords ? `${cursorCoords.lat}° N, ${cursorCoords.lng}° E` : `Center: ${center[0]}° N, ${center[1]}° E`}
        </span>
        <span className="text-slate-600">|</span>
        <span className="text-slate-300 font-semibold">{currentZoom}x</span>
        <span className="text-slate-600">|</span>
        <span className="text-emerald-400 uppercase font-sans font-bold text-[10px] tracking-wider">
          {TILE_PROVIDERS[activeTileKey]?.name}
        </span>
      </div>
    </div>
  );
}
