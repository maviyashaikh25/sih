import React, { useState, useEffect } from "react";
import { 
  BarChart3, 
  Flame, 
  Network, 
  AlertTriangle, 
  TrendingUp, 
  Activity, 
  MapPin, 
  ArrowRight,
  Clock,
  Car,
  PieChart
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid,
  BarChart,
  Bar,
  Cell
} from "recharts";
import LeafletMap from "./LeafletMap";
import { api } from "../services/api";

const VEHICLE_COLORS = {
  Car: "#00f2fe",
  Motorcycle: "#38bdf8",
  Bus: "#f59e0b",
  Truck: "#ef4444",
  Unknown: "#94a3b8"
};

export default function AnalyticsTab() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      const data = await api.getMacroAnalytics();
      setAnalytics(data);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  if (loading || !analytics) {
    return (
      <div className="text-center py-24 text-slate-500 text-sm animate-pulse">
        Computing macro traffic flow matrices and GIS heatmaps...
      </div>
    );
  }

  const vehicleChartData = analytics.vehicle_breakdown 
    ? Object.entries(analytics.vehicle_breakdown).map(([type, count]) => ({
        type,
        count,
        color: VEHICLE_COLORS[type] || "#00f2fe"
      }))
    : [
        { type: "Car", count: 68, color: "#00f2fe" },
        { type: "Motorcycle", count: 18, color: "#38bdf8" },
        { type: "Bus", count: 8, color: "#f59e0b" },
        { type: "Truck", count: 6, color: "#ef4444" }
      ];

  return (
    <div className="space-y-4">
      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="glass-card p-3.5 border-l-4 border-l-cyan-400">
          <div className="text-xs text-slate-400 font-medium">Daily Traffic Volume</div>
          <div className="text-2xl font-bold text-slate-100 font-heading mt-1">
            {analytics.total_detections_today.toLocaleString()}
          </div>
          <div className="text-[11px] text-emerald-400 mt-0.5">Automated Multi-Camera Tally</div>
        </div>

        <div className="glass-card p-3.5 border-l-4 border-l-blue-400">
          <div className="text-xs text-slate-400 font-medium">Connected Camera Nodes</div>
          <div className="text-2xl font-bold text-slate-100 font-heading mt-1">
            {analytics.active_cameras_count} Nodes
          </div>
          <div className="text-[11px] text-cyan-400 mt-0.5">Central Grid Synced</div>
        </div>

        <div className="glass-card p-3.5 border-l-4 border-l-amber-400">
          <div className="text-xs text-slate-400 font-medium">Average Corridor Speed</div>
          <div className="text-2xl font-bold text-amber-400 font-heading mt-1">
            {analytics.average_city_speed} km/h
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Peak Hour Norm: 42 km/h</div>
        </div>

        <div className="glass-card p-3.5 border-l-4 border-l-red-500">
          <div className="text-xs text-slate-400 font-medium">Active Bottleneck Spots</div>
          <div className="text-2xl font-bold text-red-400 font-heading mt-1">
            {analytics.bottlenecks.length} Critical
          </div>
          <div className="text-[11px] text-red-400 mt-0.5">AI Anomaly Triggered</div>
        </div>
      </div>

      {/* Main Row: Live GIS Density Heatmap & 12h Hourly Flow Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left 2 Cols: GIS Traffic Density Heatmap */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                City-Wide Live Traffic Density Heatmap
              </h2>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Normal</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Medium</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Congested</span>
            </div>
          </div>

          <div className="rounded-xl overflow-hidden border border-slate-800 shadow-lg">
            <LeafletMap
              heatmapPoints={analytics.heatmap}
              mode="HEATMAP"
              height="440px"
            />
          </div>
        </div>

        {/* Right 1 Col: Hourly Flow Volume Curve (Recharts) */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Hourly Flow Dynamics
            </h2>
          </div>

          <div className="glass-card p-4 h-[440px] flex flex-col justify-between">
            <div className="text-xs text-slate-400">
              Corridor vehicle throughput over past 12 hours
            </div>

            <div className="h-64 w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analytics.hourly_volume_series}>
                  <defs>
                    <linearGradient id="cyanVolume" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00f2fe" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#00f2fe" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#00f2fe", borderRadius: 8 }}
                    labelStyle={{ color: "#00f2fe", fontWeight: 700 }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="vehicles" 
                    stroke="#00f2fe" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#cyanVolume)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
              <span>Peak Corridor: <b>Ring Road AIIMS</b></span>
              <span className="text-cyan-400 font-mono">1,420 veh/hr</span>
            </div>
          </div>
        </div>
      </div>

      {/* Vehicle Classification Breakdown & Origin-Destination Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Vehicle Classification Bar Chart */}
        <div className="glass-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <Car className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Vehicle Classification
              </h3>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">AI Classified</span>
          </div>

          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={vehicleChartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" stroke="#64748b" fontSize={10} />
                <YAxis dataKey="type" type="category" stroke="#94a3b8" fontSize={11} width={75} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#00f2fe", borderRadius: 8 }}
                  formatter={(val) => [`${val} sightings`, "Count"]}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {vehicleChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-300">
            <div className="p-1.5 bg-slate-900/60 rounded border border-slate-800">
              <span className="text-cyan-400">Cars:</span> {vehicleChartData.find(v => v.type === "Car")?.count || 68}
            </div>
            <div className="p-1.5 bg-slate-900/60 rounded border border-slate-800">
              <span className="text-amber-400">Heavy:</span> {(vehicleChartData.find(v => v.type === "Truck")?.count || 6) + (vehicleChartData.find(v => v.type === "Bus")?.count || 8)}
            </div>
          </div>
        </div>

        {/* Origin - Destination (O-D) Matrix */}
        <div className="lg:col-span-2 glass-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <Network className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Origin - Destination (O-D) Trip Matrix
              </h3>
            </div>
            <span className="text-xs text-slate-400">Automated Vehicle Re-ID</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-mono text-[10px]">
                  <th className="pb-2">Origin Zone</th>
                  <th className="pb-2">Destination Zone</th>
                  <th className="pb-2 text-right">Trip Count</th>
                  <th className="pb-2 text-right">Avg Duration</th>
                  <th className="pb-2 text-right">Avg Speed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {analytics.od_matrix.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/50 transition-colors">
                    <td className="py-2.5 font-medium text-slate-200">{item.origin_zone}</td>
                    <td className="py-2.5 font-medium text-slate-200">
                      <div className="flex items-center gap-1.5">
                        <ArrowRight className="w-3 h-3 text-cyan-400" />
                        <span>{item.destination_zone}</span>
                      </div>
                    </td>
                    <td className="py-2.5 text-right font-mono text-cyan-400 font-bold">
                      {item.trip_count} trips
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-300">
                      {item.avg_travel_time_min} mins
                    </td>
                    <td className="py-2.5 text-right font-mono text-amber-400">
                      {item.avg_speed_kmh} km/h
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
