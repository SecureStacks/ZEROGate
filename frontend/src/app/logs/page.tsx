"use client";

import React, { useEffect, useState } from "react";
import { Search, Filter, AlertCircle, ShieldAlert, CheckCircle, XCircle, Key, FileText, X } from "lucide-react";
import { getAuditLogs, getAuditLogDetail } from "@/lib/api";

export default function LogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [decisionFilter, setDecisionFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  
  // Detail Modal
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  const [logDetail, setLogDetail] = useState<any>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    const params: any = { limit: 50 };
    if (decisionFilter) params.decision = decisionFilter;
    
    const data = await getAuditLogs(params);
    setLogs(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchLogs();
  }, [decisionFilter]);

  const handleOpenDetail = async (id: string) => {
    setSelectedLogId(id);
    setLoadingDetail(true);
    const detail = await getAuditLogDetail(id);
    setLogDetail(detail);
    setLoadingDetail(false);
  };

  const handleCloseDetail = () => {
    setSelectedLogId(null);
    setLogDetail(null);
  };

  const filteredLogs = logs.filter(l => 
    (l.username?.toLowerCase() || "").includes(search.toLowerCase()) || 
    (l.resource_name?.toLowerCase() || "").includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-fuchsia-400" />
            Audit Log Explorer
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Search, filter, and inspect detailed ZTNA enforcement events.
          </p>
        </div>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
        {/* Toolbar */}
        <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row gap-4 justify-between items-center bg-slate-900">
          <div className="flex items-center gap-2 w-full sm:w-96 bg-slate-950 border border-slate-700 rounded-lg p-2">
            <Search className="w-4 h-4 text-slate-500 ml-2" />
            <input 
              type="text" 
              placeholder="Search by user or resource..."
              className="bg-transparent border-none text-white text-sm focus:outline-none w-full"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-slate-500" />
            <select 
              className="bg-slate-950 border border-slate-700 rounded p-1.5 text-sm text-white focus:outline-none"
              value={decisionFilter}
              onChange={e => setDecisionFilter(e.target.value)}
            >
              <option value="">All Decisions</option>
              <option value="ALLOW">ALLOW</option>
              <option value="DENY">DENY</option>
              <option value="MFA_REQUIRED">MFA REQUIRED</option>
            </select>
          </div>
        </div>
        
        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-6 py-4 font-semibold">Timestamp</th>
                <th className="px-6 py-4 font-semibold">User</th>
                <th className="px-6 py-4 font-semibold">Resource</th>
                <th className="px-6 py-4 font-semibold">Decision</th>
                <th className="px-6 py-4 font-semibold">Segment Path</th>
                <th className="px-6 py-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                    Loading audit logs...
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                    No logs match the current filters.
                  </td>
                </tr>
              ) : (
                filteredLogs.map(log => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 text-slate-300 font-mono text-xs whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-white font-medium">{log.username}</td>
                    <td className="px-6 py-4 text-white">{log.resource_name}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-bold tracking-wider ${
                         log.decision === 'ALLOW' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                         log.decision === 'MFA_REQUIRED' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                         'bg-red-500/10 text-red-400 border border-red-500/20'
                      }`}>
                        {log.decision}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-400 text-xs">
                      {log.source_segment || '?'} &rarr; {log.destination_segment || '?'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => handleOpenDetail(log.id)}
                        className="text-fuchsia-400 hover:text-fuchsia-300 font-semibold text-xs transition-colors"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Detail Modal */}
      {selectedLogId && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
            
            <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
              <h3 className="font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-fuchsia-400" />
                Event Details
              </h3>
              <button onClick={handleCloseDetail} className="text-slate-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
              {loadingDetail || !logDetail ? (
                <div className="text-center py-12 text-slate-500">Loading details...</div>
              ) : (
                <div className="space-y-6">
                  
                  {/* Status Banner */}
                  <div className={`p-4 rounded-xl flex items-center justify-between border ${
                    logDetail.decision === 'ALLOW' ? 'bg-emerald-500/10 border-emerald-500/30' :
                    logDetail.decision === 'MFA_REQUIRED' ? 'bg-amber-500/10 border-amber-500/30' :
                    'bg-red-500/10 border-red-500/30'
                  }`}>
                    <div>
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Final Decision</div>
                      <div className={`text-xl font-black ${
                        logDetail.decision === 'ALLOW' ? 'text-emerald-400' :
                        logDetail.decision === 'MFA_REQUIRED' ? 'text-amber-400' :
                        'text-red-400'
                      }`}>
                        {logDetail.decision}
                      </div>
                      <div className="text-sm text-slate-300 mt-1">{logDetail.reason}</div>
                    </div>
                    
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white shadow-lg ${
                        logDetail.decision === 'ALLOW' ? 'bg-emerald-500' :
                        logDetail.decision === 'MFA_REQUIRED' ? 'bg-amber-500' :
                        'bg-red-500'
                    }`}>
                      {logDetail.decision === 'ALLOW' ? <CheckCircle className="w-6 h-6"/> :
                       logDetail.decision === 'MFA_REQUIRED' ? <Key className="w-6 h-6"/> :
                       <XCircle className="w-6 h-6"/>}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                      <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Context</div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Timestamp</span>
                          <span className="text-white font-mono text-xs">{new Date(logDetail.timestamp).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Event ID</span>
                          <span className="text-white font-mono text-xs truncate max-w-[120px]">{logDetail.id}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                      <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Network</div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-400">IP Address</span>
                          <span className="text-white font-mono text-xs">{logDetail.ip_address || "Unknown"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Network Type</span>
                          <span className="text-white">{logDetail.network_type || "Unknown"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Segment Path</span>
                          <span className="text-white text-xs">{logDetail.source_segment || '?'} &rarr; {logDetail.destination_segment || '?'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Entities</div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <div className="text-[10px] text-slate-500 uppercase mb-1">User</div>
                        <div className="text-sm font-semibold text-white">{logDetail.username}</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-500 uppercase mb-1">Device</div>
                        <div className="text-sm font-semibold text-white">{logDetail.device_name}</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-500 uppercase mb-1">Resource</div>
                        <div className="text-sm font-semibold text-white">{logDetail.resource_name}</div>
                      </div>
                    </div>
                  </div>
                  
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
    </div>
  );
}
