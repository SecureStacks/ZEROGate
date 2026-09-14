"use client";

import React, { useEffect, useState } from "react";
import { fetchHealth, HealthData } from "@/lib/api";
import { Activity, CheckCircle2, AlertTriangle, XCircle, RefreshCw } from "lucide-react";

export function HealthStatusBadge() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const checkStatus = async () => {
    setLoading(true);
    const data = await fetchHealth();
    setHealth(data);
    setLoading(false);
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health?.status === "healthy";
  const isDegraded = health?.status === "degraded";

  return (
    <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-full text-xs font-mono">
      <span className="flex h-2 w-2 relative">
        <span
          className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
            isHealthy
              ? "bg-emerald-400"
              : isDegraded
              ? "bg-amber-400"
              : "bg-rose-500"
          }`}
        ></span>
        <span
          className={`relative inline-flex rounded-full h-2 w-2 ${
            isHealthy
              ? "bg-emerald-500"
              : isDegraded
              ? "bg-amber-500"
              : "bg-rose-500"
          }`}
        ></span>
      </span>

      <span className="text-slate-300">
        Backend:{" "}
        <span
          className={
            isHealthy
              ? "text-emerald-400 font-semibold"
              : isDegraded
              ? "text-amber-400 font-semibold"
              : "text-rose-400 font-semibold"
          }
        >
          {loading ? "Checking..." : health?.status?.toUpperCase() || "OFFLINE"}
        </span>
      </span>

      <span className="text-slate-600">|</span>

      <span className="text-slate-400">
        DB:{" "}
        <span
          className={
            health?.database === "connected"
              ? "text-emerald-400"
              : "text-rose-400"
          }
        >
          {health?.database === "connected" ? "Connected" : "Disconnected"}
        </span>
      </span>

      <button
        onClick={checkStatus}
        title="Refresh health status"
        className="text-slate-500 hover:text-slate-300 transition-colors ml-1"
      >
        <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
      </button>
    </div>
  );
}
