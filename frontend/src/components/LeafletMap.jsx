import React, { useEffect, useRef } from "react";
import L from "leaflet";

export default function LeafletMap({
  cameras = [],
  trajectory = null,
  activePlaybackStep = null,
  heatmapPoints = [],
  center = [28.6139, 77.2090], // Default New Delhi center
  zoom = 12,
  mode = "TRAJECTORY", // 'TRAJECTORY', 'HEATMAP', 'CAMERAS'
  onCameraClick = null,
  height = "520px"
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layerGroupRef = useRef(null);

  // 1. Initialize Leaflet Map instance
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: center,
        zoom: zoom,
        zoomControl: false
      });

      L.control.zoom({ position: "bottomright" }).addTo(map);

      // CartoDB Dark Matter dark mode tile layer
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> OpenStreetMap',
        subdomains: "abcd",
        maxZoom: 19
      }).addTo(map);

      const layerGroup = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
      layerGroupRef.current = layerGroup;
    }

    return () => {
      // Clean up map on unmount
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // 2. Render Layers based on mode and props
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();

    // --- MODE 1: TRAJECTORY PLAYBACK ---
    if (mode === "TRAJECTORY" && trajectory && trajectory.points && trajectory.points.length > 0) {
      const points = trajectory.points;
      const latLngs = points.map(p => [p.latitude, p.longitude]);

      // Draw all segments polyline (Glow cyan)
      const glowLine = L.polyline(latLngs, {
        color: "#00f2fe",
        weight: 6,
        opacity: 0.85,
        smoothFactor: 1,
        dashArray: "8, 6"
      }).addTo(layerGroup);

      const baseLine = L.polyline(latLngs, {
        color: "#38bdf8",
        weight: 3,
        opacity: 0.95
      }).addTo(layerGroup);

      // Draw numbered camera pins along trajectory
      points.forEach((pt, idx) => {
        const isStart = idx === 0;
        const isEnd = idx === points.length - 1;
        const isCurrent = activePlaybackStep === idx;

        const pinColor = isStart ? "#10b981" : (isEnd ? "#ef4444" : "#38bdf8");
        const pinHtml = `
          <div style="
            background: ${pinColor};
            color: #000;
            font-weight: 800;
            font-size: 11px;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #fff;
            box-shadow: 0 0 12px ${pinColor};
            transform: translate(-50%, -50%);
          ">
            ${idx + 1}
          </div>
        `;

        const customIcon = L.divIcon({
          html: pinHtml,
          className: "trajectory-waypoint",
          iconSize: [26, 26]
        });

        const marker = L.marker([pt.latitude, pt.longitude], { icon: customIcon }).addTo(layerGroup);
        marker.bindPopup(`
          <div style="font-size: 12px;">
            <div style="color: #00f2fe; font-weight: 700;">Hop #${idx + 1}: ${pt.camera_id}</div>
            <div style="color: #cbd5e1; font-weight: 600; margin-top: 2px;">${pt.camera_name}</div>
            <div style="color: #94a3b8; font-size: 11px; margin-top: 4px;">Zone: ${pt.zone}</div>
            <div style="color: #94a3b8; font-size: 11px;">Timestamp: ${new Date(pt.timestamp).toLocaleTimeString()}</div>
            <div style="color: #fbbf24; font-size: 11px; margin-top: 2px;">Estimated Speed: ${pt.speed_estimate_kmh} km/h</div>
          </div>
        `);
      });

      // Draw current playback vehicle indicator if step selected
      if (activePlaybackStep !== null && points[activePlaybackStep]) {
        const curPt = points[activePlaybackStep];
        const vehHtml = `
          <div style="
            background: #fbbf24;
            color: #000;
            width: 38px;
            height: 38px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 3px solid #fff;
            box-shadow: 0 0 20px #fbbf24;
            animation: pulse-subtle 1.2s infinite;
            transform: translate(-50%, -50%);
          ">
            🚗
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

        const radius = Math.max(300, hp.vehicle_count * 45);

        const circle = L.circle([hp.latitude, hp.longitude], {
          color: circleColor,
          fillColor: circleColor,
          fillOpacity: 0.35 + (hp.intensity * 0.45),
          weight: 2,
          radius: radius
        }).addTo(layerGroup);

        circle.bindPopup(`
          <div style="font-size: 12px;">
            <div style="color: ${circleColor}; font-weight: 700;">${hp.camera_name}</div>
            <div style="color: #cbd5e1; margin-top: 4px;">Recent Count: <b>${hp.vehicle_count} vehicles</b> (30m)</div>
            <div style="color: #cbd5e1;">Congestion Level: <b style="color: ${circleColor};">${hp.congestion_level}</b></div>
            <div style="color: #94a3b8; font-size: 11px;">Intensity Index: ${(hp.intensity * 100).toFixed(0)}%</div>
          </div>
        `);
      });
    }

    // --- MODE 3: DEFAULT CAMERAS GRID ---
    else if (cameras && cameras.length > 0) {
      cameras.forEach(cam => {
        const camHtml = `
          <div style="
            background: #0f172a;
            color: #00f2fe;
            border: 2px solid #00f2fe;
            font-size: 12px;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
            transform: translate(-50%, -50%);
          ">
            📷
          </div>
        `;

        const camIcon = L.divIcon({
          html: camHtml,
          className: "camera-pin",
          iconSize: [30, 30]
        });

        const marker = L.marker([cam.latitude, cam.longitude], { icon: camIcon }).addTo(layerGroup);
        marker.bindPopup(`
          <div style="font-size: 12px;">
            <div style="color: #00f2fe; font-weight: 700;">${cam.id}</div>
            <div style="color: #f8fafc; font-weight: 600;">${cam.name}</div>
            <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Zone: ${cam.zone}</div>
            <div style="color: #94a3b8; font-size: 11px;">Road: ${cam.road_name || 'Corridor'}</div>
            <div style="color: #10b981; font-size: 11px; margin-top: 4px;">Status: Active (${cam.fps} FPS)</div>
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
      ref={mapContainerRef}
      style={{
        width: "100%",
        height: height,
        borderRadius: "12px",
        overflow: "hidden",
        border: "1px solid rgba(56, 189, 248, 0.2)"
      }}
    />
  );
}
