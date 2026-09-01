import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle, 
  Trash2, 
  Plus, 
  Car, 
  Clock, 
  MapPin, 
  User, 
  Search,
  CheckCircle2
} from "lucide-react";
import { api } from "../services/api";

export default function AlertsTab({
  alerts = [],
  onResolveAlert,
  onSelectPlateForTrajectory
}) {
  const [blacklist, setBlacklist] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newPlate, setNewPlate] = useState("");
  const [newReason, setNewReason] = useState("");
  const [newSeverity, setNewSeverity] = useState("HIGH");
  const [newOwner, setNewOwner] = useState("");
  const [newDetails, setNewDetails] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("ALL");

  const fetchBlacklist = async () => {
    try {
      const data = await api.getBlacklist();
      setBlacklist(data);
    } catch (e) {
      console.error("Failed to load blacklist:", e);
    }
  };

  useEffect(() => {
    fetchBlacklist();
  }, []);

  const handleAddBlacklist = async (e) => {
    e.preventDefault();
    if (!newPlate || !newReason) return;
    try {
      await api.addToBlacklist({
        plate_number: newPlate.toUpperCase().replace(/\s+/g, ""),
        reason: newReason,
        severity: newSeverity,
        owner_name: newOwner || "Unknown",
        vehicle_details: newDetails || "Unspecified Model"
      });
      setShowAddModal(false);
      setNewPlate("");
      setNewReason("");
      setNewOwner("");
      setNewDetails("");
      fetchBlacklist();
    } catch (err) {
      alert(err.message || "Failed to add to blacklist");
    }
  };

  const handleRemoveBlacklist = async (plateNumber) => {
    if (!confirm(`Are you sure you want to remove ${plateNumber} from the watchlist?`)) return;
    try {
      await api.removeFromBlacklist(plateNumber);
      fetchBlacklist();
    } catch (err) {
      alert(err.message || "Failed to remove plate");
    }
  };

  const filteredAlerts = alerts.filter(a => {
    if (filterSeverity === "ALL") return true;
    return a.severity === filterSeverity;
  });

  return (
    <div className="space-y-4">
      {/* Top Header & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 glass-card p-3.5">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-red-500 animate-pulse" />
          <div>
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Security Hotlist & Incident Dispatch Hub
            </h2>
            <p className="text-xs text-slate-400">
              Live ANPR rule-based alarms: Stolen plates, cloned teleportation & zone loitering
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white font-bold text-xs rounded-lg transition-all shadow-md shadow-red-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Flagged Vehicle</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Active Real-time Alerts & Watchlist Database */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left 2 Cols: Live Incident Alerts Stream */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Real-Time Security Alarms ({filteredAlerts.length})
              </h3>
            </div>

            {/* Severity Filter Tabs */}
            <div className="flex items-center gap-1 text-xs">
              {["ALL", "CRITICAL", "HIGH", "MEDIUM"].map((sev) => (
                <button
                  key={sev}
                  onClick={() => setFilterSeverity(sev)}
                  className={`px-2 py-0.5 rounded font-medium transition-all ${
                    filterSeverity === sev
                      ? "bg-slate-700 text-slate-100 border border-slate-600"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
            {filteredAlerts.length === 0 ? (
              <div className="glass-card p-12 text-center text-slate-500 text-xs">
                No active unresolved security alerts in this category.
              </div>
            ) : (
              filteredAlerts.map((alert, aIdx) => {
                const isResolved = alert.is_resolved;
                const isCritical = alert.severity === "CRITICAL";

                return (
                  <div
                    key={`alert-${alert.id ?? ''}-${alert.plate_number ?? ''}-${alert.timestamp ?? ''}-${aIdx}`}
                    className={`p-3.5 rounded-xl border transition-all ${
                      isResolved
                        ? "bg-slate-900/40 border-slate-800 opacity-60"
                        : isCritical
                        ? "bg-red-950/40 border-red-500/80 shadow-md shadow-red-500/10"
                        : "bg-amber-950/30 border-amber-500/60"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider font-mono ${
                            isCritical
                              ? "bg-red-500 text-white"
                              : "bg-amber-500 text-slate-950"
                          }`}
                        >
                          {alert.alert_type}
                        </span>

                        <span className="font-mono font-bold text-sm text-slate-100 px-2 py-0.5 rounded bg-slate-950 border border-slate-700">
                          {alert.plate_number}
                        </span>
                      </div>

                      <span className="text-xs text-slate-400 font-mono">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <p className="text-xs text-slate-200 font-medium mt-2">
                      {alert.message}
                    </p>

                    <div className="mt-2.5 pt-2.5 border-t border-slate-800/80 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                        <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Camera: {alert.camera_id}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => onSelectPlateForTrajectory(alert.plate_number)}
                          className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700 text-cyan-400 text-[11px] font-bold transition-all"
                        >
                          View Trajectory
                        </button>

                        {!isResolved && (
                          <button
                            onClick={() => onResolveAlert(alert.id)}
                            className="px-2.5 py-1 rounded bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/50 text-emerald-300 text-[11px] font-bold flex items-center gap-1 transition-all"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Acknowledge</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right 1 Col: Hotlist / Blacklist Registry */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Car className="w-4 h-4 text-red-400" />
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Watchlist Registry ({blacklist.length})
              </h3>
            </div>
          </div>

          <div className="glass-card p-3 max-h-[620px] overflow-y-auto space-y-2">
            {blacklist.map((item) => (
              <div
                key={item.id || item.plate_number}
                className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="font-mono font-bold text-xs text-slate-100 px-2 py-0.5 rounded bg-slate-950 border border-slate-700">
                    {item.plate_number}
                  </div>
                  <span
                    className={`text-[9px] font-bold px-1.5 py-0.2 rounded font-mono ${
                      item.severity === "CRITICAL"
                        ? "bg-red-500/20 text-red-300 border border-red-500/40"
                        : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                    }`}
                  >
                    {item.severity}
                  </span>
                </div>

                <div className="mt-1.5 text-[11px] text-slate-300 font-medium">
                  {item.reason}
                </div>

                <div className="mt-1 text-[10px] text-slate-500 flex items-center justify-between">
                  <span>{item.vehicle_details || "Unknown Vehicle"}</span>
                  <button
                    onClick={() => handleRemoveBlacklist(item.plate_number)}
                    className="text-red-400 hover:text-red-300 p-1 transition-colors"
                    title="Remove from Watchlist"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Add Flagged Vehicle Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card p-5 max-w-md w-full border border-red-500/40 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-500" /> Add Vehicle to Hotlist
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddBlacklist} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">License Plate Number *</label>
                <input
                  type="text"
                  required
                  value={newPlate}
                  onChange={(e) => setNewPlate(e.target.value.toUpperCase())}
                  placeholder="e.g. DL01AB1234"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 font-mono text-slate-100 focus:outline-none focus:border-red-400"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Reason for Flagging *</label>
                <input
                  type="text"
                  required
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  placeholder="e.g. Stolen Vehicle, FIR #204 Robbery Suspect"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-red-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Severity Level</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-red-400"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Owner Name</label>
                  <input
                    type="text"
                    value={newOwner}
                    onChange={(e) => setNewOwner(e.target.value)}
                    placeholder="e.g. Unknown / Stolen"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-red-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Vehicle Make / Model</label>
                <input
                  type="text"
                  value={newDetails}
                  onChange={(e) => setNewDetails(e.target.value)}
                  placeholder="e.g. Black Mahindra Scorpio N"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-100 focus:outline-none focus:border-red-400"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 font-bold text-white shadow-md shadow-red-600/30"
                >
                  Confirm Watchlist Add
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
