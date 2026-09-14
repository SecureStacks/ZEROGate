"use client";

import React, { useEffect, useState, useRef, useLayoutEffect } from "react";
import { Network, Server, User as UserIcon, Smartphone, ShieldCheck, Activity, Target, ArrowRightCircle, ChevronDown } from "lucide-react";
import { getTopology } from "@/lib/api";

export default function TopologyPage() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [latestRequest, setLatestRequest] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedIdentityId, setSelectedIdentityId] = useState<string>("");
  
  const [nodeRects, setNodeRects] = useState<Record<string, {x: number, y: number, w: number, h: number}>>({});
  const containerRef = useRef<HTMLDivElement>(null);

  const fetchData = async () => {
    try {
      const data = await getTopology();
      setNodes(data.nodes);
      setEdges(data.edges);
      setLatestRequest(data.latest_request);
      setLoading(false);
      
      // Auto-select first user if none selected
      if (!selectedIdentityId && data.nodes) {
        const users = data.nodes.filter((n: any) => n.type === 'user');
        if (users.length > 0) {
           setSelectedIdentityId(users[0].id);
        }
      }
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [selectedIdentityId]);

  const updateRects = () => {
    if (!containerRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const newRects: Record<string, any> = {};
    const elements = containerRef.current.querySelectorAll('[data-node-id]');
    elements.forEach(el => {
        const id = el.getAttribute('data-node-id');
        const rect = el.getBoundingClientRect();
        if (id) {
            newRects[id] = {
                x: rect.left - containerRect.left + containerRef.current!.scrollLeft,
                y: rect.top - containerRect.top + containerRef.current!.scrollTop,
                w: rect.width,
                h: rect.height
            };
        }
    });
    setNodeRects(newRects);
  };

  useLayoutEffect(() => {
    if (!loading) {
      setTimeout(updateRects, 100);
    }
  }, [nodes, edges, loading, selectedIdentityId]);

  useEffect(() => {
    window.addEventListener('resize', updateRects);
    return () => window.removeEventListener('resize', updateRects);
  }, []);

  const allUsers = nodes.filter(n => n.type === 'user');
  const allDevices = nodes.filter(n => n.type === 'device');
  const pep = nodes.filter(n => n.type === 'gateway');
  const security = nodes.filter(n => n.type === 'security');
  const segments = nodes.filter(n => n.type === 'segment');
  const resources = nodes.filter(n => n.type === 'resource');

  const riskEngine = security.find(s => s.id === 'risk_engine');
  const pdp = security.find(s => s.id === 'pdp');

  // Filter visible nodes to strictly the selected user
  const visibleUsers = allUsers.filter(u => u.id === selectedIdentityId);
  const visibleDevices = allDevices.filter(d => 
    d.metadata?.owner_user_id === selectedIdentityId?.replace('user_', '')
  );

  const selectedIdentityData = allUsers.find(u => u.id === selectedIdentityId);
  const selectedIdentityDevicesCount = allDevices.filter(d => d.metadata?.owner_user_id === selectedIdentityId?.replace('user_', '')).length;
  
  const isBreach = latestRequest?.pep_status === 'BLOCKED' || latestRequest?.segmentation_status === 'MICROSEGMENTATION BLOCKED';

  return (
    <div className="space-y-6 flex flex-col h-full min-h-screen pb-10">
      
      {/* Header & Controls */}
      <div className="flex flex-col xl:flex-row xl:items-start gap-6 shrink-0">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5 mb-2">
            <Network className="w-6 h-6 text-emerald-400" />
            Live Access Topology
          </h1>
          <p className="text-sm text-slate-400 max-w-3xl">
            Every access request is evaluated using identity, device posture, network context, risk and policy before the PEP enforces access to a microsegmented resource.
          </p>
          <div className="flex items-center gap-2 text-xs font-bold text-slate-500 mt-3">
             <span>IDENTITY</span><ArrowRightCircle className="w-3 h-3"/>
             <span>DEVICE</span><ArrowRightCircle className="w-3 h-3"/>
             <span>ZTNA GATEWAY</span><ArrowRightCircle className="w-3 h-3"/>
             <span>RISK + PDP</span><ArrowRightCircle className="w-3 h-3"/>
             <span>SEGMENT</span><ArrowRightCircle className="w-3 h-3"/>
             <span>RESOURCE</span>
          </div>
        </div>

        <div className="flex items-center gap-4 bg-slate-900 border border-slate-700 p-4 rounded-xl">
           <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Current Identity View</label>
              <div className="relative">
                 <select 
                   value={selectedIdentityId}
                   onChange={(e) => setSelectedIdentityId(e.target.value)}
                   className="appearance-none bg-slate-950 border border-slate-700 text-white text-sm font-bold rounded-lg px-4 py-2 pr-10 outline-none focus:border-indigo-500 cursor-pointer w-64"
                 >
                   {allUsers.map(u => (
                     <option key={u.id} value={u.id}>{u.label} — {u.metadata?.role || 'User'}</option>
                   ))}
                 </select>
                 <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-2.5 pointer-events-none"/>
              </div>
           </div>
        </div>
      </div>

      <div className="flex flex-col xl:flex-row gap-6 flex-1 min-h-0">
        
        {/* Main Topology Graph */}
        <div 
          ref={containerRef}
          onScroll={updateRects}
          className="flex-1 bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden relative p-8 min-h-[500px] shadow-2xl"
        >
          {loading ? (
             <div className="text-slate-500 w-full h-full flex items-center justify-center">Loading topology...</div>
          ) : (
            <div className="w-full h-full flex items-start justify-between gap-4 relative z-10">
               
               {/* Column 1: Identities */}
               <div className="flex flex-col gap-6 z-10 w-44">
                 <div className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-800 pb-2">Identities</div>
                 {visibleUsers.map(u => {
                   const isLatest = latestRequest && u.id === latestRequest.user_id;
                   const isSelected = selectedIdentityId === u.id;
                   
                   return (
                   <div 
                     key={u.id} data-node-id={u.id} onClick={() => setSelectedNode(u)}
                     className={`p-3 rounded-lg border cursor-pointer transition-all shadow-lg flex flex-col gap-2 relative ${
                       selectedNode?.id === u.id ? 'ring-2 ring-white bg-slate-800' : 'bg-slate-950'
                     } ${isLatest ? 'border-indigo-500 bg-indigo-950/20' : isSelected ? 'border-slate-500' : 'border-slate-800 opacity-50'}`}
                   >
                     {isLatest && <div className="absolute -top-2 -right-2 w-3 h-3 bg-indigo-500 rounded-full animate-pulse border-2 border-slate-900"></div>}
                     <div className="flex items-center gap-2">
                       <UserIcon className={`w-4 h-4 ${isLatest ? 'text-indigo-400' : 'text-slate-400'}`}/>
                       <div className="text-sm font-bold text-white truncate">{u.label}</div>
                     </div>
                     <div className="text-[10px] text-slate-400 uppercase tracking-wide">{u.metadata?.role || 'User'}</div>
                   </div>
                 )})}
               </div>
               
               {/* Column 2: Devices */}
               <div className="flex flex-col gap-4 z-10 w-52">
                 <div className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-800 pb-2">Devices</div>
                 {visibleDevices.map(d => {
                   const isLatest = latestRequest && d.id === latestRequest.device_id;
                   const isOwnerSelected = d.metadata?.owner_user_id === selectedIdentityId?.replace('user_', '');
                   
                   return (
                   <div 
                     key={d.id} data-node-id={d.id} onClick={() => setSelectedNode(d)}
                     className={`p-3 rounded-lg border cursor-pointer transition-all shadow-lg flex flex-col gap-2 relative ${
                       selectedNode?.id === d.id ? 'ring-2 ring-white bg-slate-800' : 'bg-slate-950'
                     } ${isLatest ? (isBreach ? 'border-red-500 bg-red-950/20' : 'border-indigo-500 bg-indigo-950/20') : isOwnerSelected ? 'border-slate-600' : 'border-slate-800 opacity-50'}`}
                   >
                     <div className="flex items-center gap-2">
                       <Smartphone className={`w-4 h-4 ${isLatest ? (isBreach ? 'text-red-400' : 'text-indigo-400') : 'text-slate-400'}`}/>
                       <div className="text-sm font-bold text-white truncate">{d.label}</div>
                     </div>
                     <div className="text-[10px] text-slate-400 flex flex-col gap-1">
                       <span>Owner: {allUsers.find(u => u.id === `user_${d.metadata?.owner_user_id}`)?.label || d.label.split(' ')[0]}</span>
                       <span className={d.metadata?.posture === 'HEALTHY' ? 'text-emerald-400 font-bold' : d.metadata?.posture === 'COMPROMISED' ? 'text-red-400 font-bold' : 'text-amber-400 font-bold'}>{d.metadata?.posture || 'UNKNOWN'}</span>
                       <span>{d.metadata?.managed ? 'MANAGED' : 'UNMANAGED'}</span>
                     </div>
                     {isLatest && (
                       <div className={`text-[9px] font-bold mt-1 px-1.5 py-0.5 rounded w-fit ${isBreach ? 'bg-red-900/50 text-red-300' : 'bg-indigo-900/50 text-indigo-300'}`}>
                         ● LATEST REQUEST
                       </div>
                     )}
                   </div>
                 )})}
               </div>
               
               {/* Column 3: PEP */}
               <div className="flex flex-col gap-6 z-10 w-44 pt-16">
                 <div className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-800 pb-2">ZTNA Gateway</div>
                 {pep.map(p => {
                    return (
                   <div 
                     key={p.id} data-node-id={p.id} onClick={() => setSelectedNode(p)}
                     className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center justify-center gap-2 shadow-2xl ${
                       selectedNode?.id === p.id ? 'ring-2 ring-white bg-slate-800' : 'bg-slate-950 border-slate-600'
                     } ${latestRequest ? 'border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : ''}`}
                   >
                     <ShieldCheck className={`w-8 h-8 ${latestRequest ? 'text-emerald-400' : 'text-slate-500'}`}/>
                     <div className="text-center">
                       <div className="text-sm font-bold text-white">{p.label}</div>
                     </div>
                   </div>
                 )})}
               </div>

               {/* Column 4: Risk & PDP */}
               <div className="flex flex-col gap-8 z-10 w-48 pt-4">
                 <div className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-800 pb-2">Security Decision</div>
                 
                 {riskEngine && (
                   <div 
                     key={riskEngine.id} data-node-id={riskEngine.id} onClick={() => setSelectedNode(riskEngine)}
                     className={`p-3 rounded-lg border-2 cursor-pointer transition-all flex flex-col items-center justify-center gap-2 shadow-xl ${
                       selectedNode?.id === riskEngine.id ? 'ring-2 ring-white bg-slate-800' : 'bg-slate-950 border-slate-700'
                     } ${latestRequest ? 'border-indigo-500/50' : ''}`}
                   >
                     <Activity className="w-5 h-5 text-indigo-400"/>
                     <div className="text-sm font-bold text-white text-center">{riskEngine.label}</div>
                     {latestRequest && (
                        <div className={`text-xs font-bold mt-1 px-2 py-1 rounded w-full text-center border ${
                          latestRequest.risk_level === 'HIGH' ? 'bg-red-950 text-red-400 border-red-500/30' : 
                          latestRequest.risk_level === 'MEDIUM' ? 'bg-amber-950 text-amber-400 border-amber-500/30' : 
                          'bg-emerald-950 text-emerald-400 border-emerald-500/30'
                        }`}>
                          Score: {latestRequest.risk_score} ({latestRequest.risk_level})
                        </div>
                     )}
                   </div>
                 )}

                 {pdp && (
                   <div 
                     key={pdp.id} data-node-id={pdp.id} onClick={() => setSelectedNode(pdp)}
                     className={`p-3 rounded-lg border-2 cursor-pointer transition-all flex flex-col items-center justify-center gap-2 shadow-xl ${
                       selectedNode?.id === pdp.id ? 'ring-2 ring-white bg-slate-800' : 'bg-slate-950 border-slate-700'
                     } ${latestRequest ? 'border-indigo-500/50' : ''}`}
                   >
                     <Target className="w-5 h-5 text-indigo-400"/>
                     <div className="text-sm font-bold text-white text-center">{pdp.label}</div>
                     {latestRequest && (
                        <div className={`text-xs font-bold mt-1 px-2 py-1 rounded w-full text-center border ${
                          latestRequest.pdp_decision === 'ALLOW' ? 'bg-emerald-950 text-emerald-400 border-emerald-500/30' :
                          latestRequest.pdp_decision === 'MFA_REQUIRED' ? 'bg-amber-950 text-amber-400 border-amber-500/30' : 
                          'bg-red-950 text-red-400 border-red-500/30'
                        }`}>
                          {latestRequest.pdp_decision}
                        </div>
                     )}
                   </div>
                 )}
               </div>

               {/* Column 5: Microsegments */}
               <div className="flex flex-col gap-6 z-10 w-48 pt-2">
                 <div className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-800 pb-2">Microsegmentation</div>
                 {segments.map(seg => {
                   const isTargetSegment = latestRequest?.target_segment && seg.id === `segment_${latestRequest.target_segment}`;
                   const isBlockedHere = isTargetSegment && latestRequest?.segmentation_status === 'MICROSEGMENTATION BLOCKED';
                   
                   return (
                   <div 
                     key={seg.id} data-node-id={seg.id} onClick={() => setSelectedNode(seg)}
                     className={`p-3 rounded-lg border-2 border-dashed cursor-pointer transition-all flex flex-col gap-1 shadow-lg ${
                       selectedNode?.id === seg.id ? 'ring-2 ring-white bg-slate-800 border-solid' : 'bg-slate-950/50 border-slate-700'
                     } ${isBlockedHere ? 'border-red-500/80 bg-red-950/20' : isTargetSegment ? 'border-emerald-500/50 bg-emerald-950/10' : 'opacity-60'}`}
                   >
                     <div className="text-sm font-bold text-white break-words">{seg.label}</div>
                     <div className="text-[10px] text-slate-400">Segment Zone</div>
                     {isBlockedHere && <div className="text-[10px] font-bold text-red-500 mt-2 bg-red-950/80 p-1 rounded inline-block text-center border border-red-900 uppercase">BLOCKED BY PEP</div>}
                   </div>
                 )})}
               </div>
               
               {/* Column 6: Resources */}
               <div className="flex flex-col gap-4 z-10 w-48">
                 <div className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-800 pb-2">Protected Resources</div>
                 {resources.map(r => {
                   const isLatest = latestRequest && r.id === latestRequest.resource_id;
                   let statusClass = 'border-slate-800 opacity-60';
                   let statusText = null;
                   
                   if (isLatest) {
                     if (latestRequest.pep_status === 'ALLOWED') {
                       statusClass = 'border-emerald-500 bg-emerald-950/20 opacity-100 shadow-[0_0_15px_rgba(16,185,129,0.2)]';
                       statusText = <span className="text-emerald-400 font-bold mt-1">ACCESS GRANTED</span>;
                     } else if (latestRequest.pep_status === 'PENDING MFA') {
                       statusClass = 'border-amber-500 bg-amber-950/20 opacity-100 shadow-[0_0_15px_rgba(245,158,11,0.2)]';
                       statusText = <span className="text-amber-400 font-bold mt-1">WAITING FOR MFA</span>;
                     } else {
                       statusClass = 'border-red-500 bg-red-950/20 opacity-100 shadow-[0_0_15px_rgba(239,68,68,0.2)]';
                       statusText = <span className="text-red-400 font-bold mt-1">ACCESS DENIED</span>;
                     }
                   }
                   
                   return (
                   <div 
                     key={r.id} data-node-id={r.id} onClick={() => setSelectedNode(r)}
                     className={`p-3 rounded-lg border cursor-pointer transition-all shadow-lg flex flex-col gap-1.5 relative ${
                       selectedNode?.id === r.id ? 'ring-2 ring-white bg-slate-800 opacity-100' : 'bg-slate-950'
                     } ${statusClass}`}
                   >
                     <div className="flex items-center gap-2">
                       <Server className={`w-4 h-4 ${isLatest && latestRequest.pep_status === 'ALLOWED' ? 'text-emerald-400' : 'text-slate-400'}`}/>
                       <div className="text-sm font-bold text-white truncate">{r.label}</div>
                     </div>
                     <div className="text-[10px] text-slate-400 flex flex-col">
                       <span>Segment: {r.metadata?.segment || 'NONE'}</span>
                       {statusText}
                     </div>
                   </div>
                 )})}
               </div>
               
               {/* SVG Edges Overlay */}
               <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
                  <defs>
                    <marker id="arrow-active" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill="#6366f1" />
                    </marker>
                    <marker id="arrow-allow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill="#10b981" />
                    </marker>
                    <marker id="arrow-mfa" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill="#f59e0b" />
                    </marker>
                    <marker id="arrow-block" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill="#ef4444" />
                    </marker>
                  </defs>
                  
                  {latestRequest && latestRequest.user_id === selectedIdentityId && (() => {
                     // Draw ONLY the active path derived perfectly from latestRequest
                     const paths: any[] = [];
                     
                     // 1. User -> Device
                     if (nodeRects[latestRequest.user_id] && nodeRects[latestRequest.device_id]) {
                         paths.push({src: latestRequest.user_id, tgt: latestRequest.device_id, color: '#6366f1', marker: 'url(#arrow-active)'});
                     }
                     // 2. Device -> PEP
                     if (nodeRects[latestRequest.device_id] && nodeRects['pep_gateway']) {
                         paths.push({src: latestRequest.device_id, tgt: 'pep_gateway', color: '#6366f1', marker: 'url(#arrow-active)'});
                     }
                     // 3. PEP -> Risk
                     if (nodeRects['pep_gateway'] && nodeRects['risk_engine']) {
                         paths.push({src: 'pep_gateway', tgt: 'risk_engine', color: '#6366f1', marker: 'url(#arrow-active)'});
                     }
                     // 4. Risk -> PDP
                     if (nodeRects['risk_engine'] && nodeRects['pdp']) {
                         paths.push({src: 'risk_engine', tgt: 'pdp', color: '#6366f1', marker: 'url(#arrow-active)'});
                     }
                     
                     // 5. PDP -> Segment
                     const segmentId = `segment_${latestRequest.target_segment}`;
                     let statusColor = '#ef4444';
                     let marker = 'url(#arrow-block)';
                     if (latestRequest.pep_status === 'ALLOWED') { statusColor = '#10b981'; marker = 'url(#arrow-allow)'; }
                     else if (latestRequest.pep_status === 'PENDING MFA') { statusColor = '#f59e0b'; marker = 'url(#arrow-mfa)'; }
                     
                     if (nodeRects['pdp'] && nodeRects[segmentId]) {
                         paths.push({src: 'pdp', tgt: segmentId, color: statusColor, marker: marker});
                     }
                     
                     // 6. Segment -> Resource (Only if not blocked)
                     if (latestRequest.pep_status !== 'BLOCKED' && nodeRects[segmentId] && nodeRects[latestRequest.resource_id]) {
                         paths.push({src: segmentId, tgt: latestRequest.resource_id, color: statusColor, marker: marker});
                     }
                     
                     return paths.map((p, idx) => {
                        const srcNode = nodeRects[p.src];
                        const tgtNode = nodeRects[p.tgt];
                        const x1 = srcNode.x + srcNode.w;
                        const y1 = srcNode.y + srcNode.h / 2;
                        const x2 = tgtNode.x;
                        const y2 = tgtNode.y + tgtNode.h / 2;
                        const path = `M ${x1} ${y1} C ${x1 + 30} ${y1}, ${x2 - 30} ${y2}, ${x2} ${y2}`;
                        
                        return (
                            <path 
                               key={`path_${idx}`} 
                               d={path} 
                               fill="none" 
                               stroke={p.color} 
                               strokeWidth={2.5}
                               markerEnd={p.marker}
                            />
                        );
                     });
                  })()}
               </svg>

            </div>
          )}
        </div>
        
        {/* Right Status Sidebar */}
        <div className="xl:w-72 shrink-0 flex flex-col gap-6">
          
          {/* Identity Summary Card */}
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 shadow-xl">
            <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-800 pb-2">
               Selected Identity
            </div>
            {selectedIdentityData ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                   <span className="text-lg font-bold text-white">{selectedIdentityData.label}</span>
                   <span className="text-xs text-indigo-400 uppercase font-bold">{selectedIdentityData.metadata?.role}</span>
                </div>
                <div className="flex items-center justify-between">
                   <span className="text-xs text-slate-400">Registered Devices</span>
                   <span className="text-sm font-bold text-white">{selectedIdentityDevicesCount}</span>
                </div>
              </div>
            ) : (
              <div className="text-sm text-slate-500 italic">No identity selected.</div>
            )}
          </div>

          {/* Latest Request Status Card - Uses purely latestRequest single source of truth */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
             <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4 border-b border-slate-800 pb-2">
               Latest Access Request
             </div>
             
             {!latestRequest ? (
                <div className="text-sm text-slate-500 italic">No recent requests.</div>
             ) : (
                <div className="space-y-4">
                  <div className="flex flex-col">
                     <span className="text-[10px] text-slate-400 uppercase">Identity</span>
                     <span className="text-sm font-bold text-white">{allUsers.find(u => u.id === latestRequest.user_id)?.label || 'Unknown'}</span>
                  </div>
                  <div className="flex flex-col">
                     <span className="text-[10px] text-slate-400 uppercase">Device</span>
                     <span className="text-sm font-bold text-white truncate">{allDevices.find(d => d.id === latestRequest.device_id)?.label || 'Unknown'}</span>
                  </div>
                  <div className="flex flex-col">
                     <span className="text-[10px] text-slate-400 uppercase">Target</span>
                     <span className="text-sm font-bold text-white truncate">{resources.find(r => r.id === latestRequest.resource_id)?.label || 'Unknown'}</span>
                  </div>
                  
                  <div className="border-t border-slate-800 pt-4 flex flex-col gap-2">
                     <div className="flex justify-between items-center bg-slate-950 p-2 rounded">
                        <span className="text-[11px] text-slate-400 font-bold uppercase">Risk</span>
                        <span className={`text-[11px] font-bold ${latestRequest.risk_level === 'HIGH' ? 'text-red-400' : latestRequest.risk_level === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'}`}>
                          {latestRequest.risk_level} · {latestRequest.risk_score}
                        </span>
                     </div>
                     <div className="flex justify-between items-center bg-slate-950 p-2 rounded">
                        <span className="text-[11px] text-slate-400 font-bold uppercase">PDP</span>
                        <span className={`text-[11px] font-bold ${latestRequest.pdp_decision === 'ALLOW' ? 'text-emerald-400' : latestRequest.pdp_decision === 'MFA_REQUIRED' ? 'text-amber-400' : 'text-red-400'}`}>
                           {latestRequest.pdp_decision}
                        </span>
                     </div>
                     <div className="flex justify-between items-center bg-slate-950 p-2 rounded">
                        <span className="text-[11px] text-slate-400 font-bold uppercase">PEP</span>
                        <span className={`text-[11px] font-bold ${latestRequest.pep_status === 'ALLOWED' ? 'text-emerald-400' : latestRequest.pep_status === 'PENDING MFA' ? 'text-amber-400' : 'text-red-400'}`}>
                           {latestRequest.pep_status}
                        </span>
                     </div>
                     <div className="flex justify-between items-center bg-slate-950 p-2 rounded">
                        <span className="text-[11px] text-slate-400 font-bold uppercase">Segmentation</span>
                        <span className={`text-[11px] font-bold ${latestRequest.segmentation_status === 'ALLOWED' ? 'text-emerald-400' : latestRequest.segmentation_status === 'PENDING' ? 'text-amber-400' : 'text-red-400'}`}>
                           {latestRequest.segmentation_status}
                        </span>
                     </div>
                  </div>
                </div>
             )}
          </div>

          {/* Node Details */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex-1">
            <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-800 pb-2">
              Node Details
            </div>
            
            {!selectedNode ? (
              <div className="text-sm text-slate-500 italic">
                Click any node in the graph for details.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-slate-950 rounded p-4 border border-slate-800">
                  <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">{selectedNode.type}</div>
                  <div className="text-base font-bold text-white break-words">{selectedNode.label}</div>
                </div>
                
                <div className="space-y-2">
                  {Object.entries(selectedNode.metadata || {}).map(([key, val]) => {
                     // Prettify device owner resolution
                     let displayVal = String(val);
                     if (key === 'owner_user_id') {
                        displayVal = allUsers.find(u => u.id === `user_${val}`)?.label || displayVal;
                     }
                     return (
                      <div key={key} className="bg-slate-950 rounded p-2.5 border border-slate-800 flex flex-col gap-1">
                        <span className="text-[10px] text-slate-500 font-bold uppercase">{key.replace(/_/g, ' ')}</span>
                        <span className="text-xs font-bold text-white truncate">{displayVal}</span>
                      </div>
                     );
                  })}
                </div>
              </div>
            )}
          </div>
          
        </div>
      </div>

      {/* Lateral Movement Protection Box */}
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 shadow-lg max-w-4xl">
         <div className="text-sm font-bold text-white mb-2 uppercase tracking-wide flex items-center gap-2">
           <ShieldCheck className="w-5 h-5 text-emerald-500"/>
           Lateral Movement Protection
         </div>
         <p className="text-sm text-slate-400 mb-4">
           Users and compromised devices cannot move laterally between microsegments unless an explicit policy permits the connection. ZeroGate PEP intercepts and drops unauthorized cross-segment requests.
         </p>
         
         <div className="flex flex-col sm:flex-row items-center gap-6 p-5 bg-slate-950 rounded border border-slate-800 w-fit">
            <div className="flex flex-col gap-1 items-center sm:items-start text-center sm:text-left min-w-[180px]">
               <span className="text-[10px] font-bold text-slate-500 uppercase">Source</span>
               <span className="text-sm font-bold text-white truncate max-w-[200px]">
                 {latestRequest?.pep_status === 'BLOCKED' ? (allUsers.find(u => u.id === latestRequest.user_id)?.label || 'Compromised Session') : 'Any Authorized User'}
               </span>
               <span className="text-xs text-slate-400">
                 Segment: {latestRequest?.pep_status === 'BLOCKED' ? latestRequest.source_segment : 'Origin Segment'}
               </span>
            </div>
            
            <div className="flex flex-col items-center gap-1 min-w-[200px]">
               <ArrowRightCircle className={`w-8 h-8 ${latestRequest?.pep_status === 'BLOCKED' ? 'text-red-500' : 'text-slate-600'}`}/>
               {latestRequest?.pep_status === 'BLOCKED' ? (
                 <div className="flex flex-col items-center gap-1 mt-1">
                   <span className="text-[10px] font-bold text-red-400 bg-red-950 px-2 py-0.5 rounded border border-red-900 uppercase">MICROSEGMENTATION BLOCKED</span>
                   <span className="text-[10px] text-red-300 text-center italic">{latestRequest.reason}</span>
                 </div>
               ) : (
                 <span className="text-[10px] font-bold text-slate-500 mt-1 uppercase tracking-widest">No Lateral Movement</span>
               )}
            </div>
            
            <div className="flex flex-col gap-1 items-center sm:items-start text-center sm:text-left min-w-[180px]">
               <span className="text-[10px] font-bold text-slate-500 uppercase">Target</span>
               <span className="text-sm font-bold text-white truncate max-w-[200px]">
                 {latestRequest?.pep_status === 'BLOCKED' ? (resources.find(r => r.id === latestRequest.resource_id)?.label || 'Protected Resource') : 'Target Resource'}
               </span>
               <span className="text-xs text-slate-400">
                 Segment: {latestRequest?.pep_status === 'BLOCKED' ? latestRequest.target_segment : 'Target Segment'}
               </span>
            </div>
         </div>
      </div>

    </div>
  );
}
