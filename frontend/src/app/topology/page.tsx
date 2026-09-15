"use client";

import React, { useEffect, useState, useRef, useLayoutEffect } from "react";
import { Network, Server, User as UserIcon, Smartphone, ShieldCheck, Activity, Target, ArrowRightCircle } from "lucide-react";
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
      setNodes(data.nodes || []);
      setEdges(data.edges || []);
      setLatestRequest(data.latest_request || null);
      setLoading(false);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  // Set initial selected identity
  useEffect(() => {
    if (!selectedIdentityId && nodes.length > 0) {
      const users = nodes.filter(n => n.type === 'user');
      if (users.length > 0) {
        setSelectedIdentityId(users[0].id);
      }
    }
  }, [nodes, selectedIdentityId]);

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
      const timeout = setTimeout(updateRects, 150);
      return () => clearTimeout(timeout);
    }
  }, [nodes, edges, loading, selectedIdentityId]);

  useEffect(() => {
    window.addEventListener('resize', updateRects);
    return () => window.removeEventListener('resize', updateRects);
  }, []);

  // Classify nodes
  const allUsers = nodes.filter(n => n.type === 'user');
  const allDevices = nodes.filter(n => n.type === 'device');
  const pepNodes = nodes.filter(n => n.type === 'gateway');
  const riskEngine = nodes.find(n => n.id === 'risk_engine');
  const pdp = nodes.find(n => n.id === 'pdp');
  const segments = nodes.filter(n => n.type === 'segment');
  const resources = nodes.filter(n => n.type === 'resource');

  // Selected User Logic
  // Find devices owned by the selected user based on innate edges returned by backend
  const userDeviceEdges = edges.filter(e => e.source === selectedIdentityId && e.target.startsWith('device_'));
  const userDeviceIds = new Set(userDeviceEdges.map(e => e.target));
  const visibleDevices = allDevices.filter(d => userDeviceIds.has(d.id));
  
  const selectedIdentityData = allUsers.find(u => u.id === selectedIdentityId);

  // Canonical Security State from latestRequest
  const securityState = latestRequest ? {
    riskScore: latestRequest.risk_score || 0,
    riskLevel: latestRequest.risk_level || 'UNKNOWN',
    pdpDecision: latestRequest.pdp_decision || 'UNKNOWN',
    pepState: latestRequest.pep_status || 'UNKNOWN',
    segmentationState: latestRequest.segmentation_status || 'UNKNOWN',
    isAllow: latestRequest.pep_status === 'ALLOWED',
    isMfa: latestRequest.pep_status === 'PENDING MFA',
    isDeny: latestRequest.pep_status === 'BLOCKED' || latestRequest.segmentation_status === 'MICROSEGMENTATION BLOCKED',
    targetSegment: `segment_${latestRequest.target_segment}`
  } : null;

  // Active path colors
  const COLOR_ALLOW = '#10b981';
  const COLOR_MFA = '#f59e0b';
  const COLOR_DENY = '#ef4444';
  const COLOR_NEUTRAL = '#475569';
  
  const getPathColor = () => {
    if (!securityState) return COLOR_NEUTRAL;
    if (securityState.isAllow) return COLOR_ALLOW;
    if (securityState.isMfa) return COLOR_MFA;
    return COLOR_DENY;
  };
  const activeColor = getPathColor();

  let pepVisualStatus = null;
  let pepColorClass = 'border-slate-700';
  let pepShadowClass = '';
  let pepIconColorClass = 'text-slate-500';
  let pepBgClass = 'bg-slate-800/50';

  if (securityState) {
    if (securityState.pdpDecision === 'ALLOW' || securityState.pepState === 'ALLOWED') {
      pepVisualStatus = 'ALLOWED';
      pepColorClass = 'border-emerald-500/50 ring-2 ring-emerald-500/20';
      pepShadowClass = 'shadow-[0_0_20px_rgba(16,185,129,0.15)]';
      pepIconColorClass = 'text-emerald-400';
      pepBgClass = 'bg-emerald-500/10';
    } else if (securityState.pdpDecision === 'MFA_REQUIRED' && securityState.pepState === 'PENDING MFA') {
      pepVisualStatus = 'PENDING MFA';
      pepColorClass = 'border-amber-500/50 ring-2 ring-amber-500/20';
      pepShadowClass = 'shadow-[0_0_20px_rgba(245,158,11,0.15)]';
      pepIconColorClass = 'text-amber-400';
      pepBgClass = 'bg-amber-500/10';
    } else if (securityState.pdpDecision === 'DENY' || securityState.pepState === 'BLOCKED') {
      pepVisualStatus = 'BLOCKED';
      pepColorClass = 'border-red-500/50 ring-2 ring-red-500/20';
      pepShadowClass = 'shadow-[0_0_20px_rgba(239,68,68,0.15)]';
      pepIconColorClass = 'text-red-400';
      pepBgClass = 'bg-red-500/10';
    }
  }

  return (
    <div className="space-y-6 flex flex-col h-full min-h-screen pb-10 bg-[#020617]">
      {/* Header */}
      <div className="shrink-0 px-6 pt-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2.5 mb-1">
          <Network className="w-6 h-6 text-cyan-400" />
          System Topology & Access Flow
        </h1>
        <p className="text-sm text-slate-400 max-w-3xl">
          Visual representation of ZeroGate's Zero Trust architecture and real-time access decision flow.
        </p>
      </div>

      <div className="flex flex-col xl:flex-row gap-6 flex-1 px-6 min-h-0">
        {/* Main Topology Graph */}
        <div 
          ref={containerRef}
          onScroll={updateRects}
          className="flex-1 bg-[#0b1120] border border-slate-800 rounded-xl overflow-x-auto overflow-y-hidden relative p-8 shadow-2xl min-w-0"
        >
          {loading ? (
             <div className="text-slate-500 w-full h-full flex items-center justify-center">Loading topology...</div>
          ) : (
            <div className="min-w-max h-full flex items-start justify-between gap-8 relative z-10">
               
               {/* Column 1A: Identities */}
               <div className="flex flex-col gap-4 z-10 w-48">
                 <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 border-b border-slate-800 pb-2">Identities</div>
                 <div className="text-[10px] text-slate-500 mb-2">Users requesting access</div>
                 {allUsers.map(u => {
                   const isSelected = selectedIdentityId === u.id;
                   return (
                   <div 
                     key={u.id} data-node-id={u.id} onClick={() => { setSelectedIdentityId(u.id); setSelectedNode(u); }}
                     className={`p-3 rounded-xl border cursor-pointer transition-all shadow-lg flex items-center gap-3 relative ${
                       isSelected ? 'border-cyan-500 bg-cyan-950/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]' : 'border-slate-800 bg-slate-900/50 hover:bg-slate-800 opacity-60'
                     }`}
                   >
                     <div className={`p-2 rounded-lg ${isSelected ? 'bg-cyan-500/20 text-cyan-400' : 'bg-slate-800 text-slate-400'}`}>
                        <UserIcon className="w-5 h-5"/>
                     </div>
                     <div className="flex flex-col overflow-hidden">
                       <div className="text-sm font-bold text-white truncate">{u.label}</div>
                       <div className="text-[10px] text-slate-400 uppercase tracking-wide truncate">{u.metadata?.role || 'User'}</div>
                     </div>
                   </div>
                 )})}
               </div>
               
               {/* Column 1B: Devices */}
               <div className="flex flex-col gap-4 z-10 w-52">
                 <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 border-b border-slate-800 pb-2">Devices</div>
                 <div className="text-[10px] text-slate-500 mb-2">Registered devices</div>
                 {visibleDevices.length === 0 ? (
                    <div className="text-xs text-slate-600 italic">No devices found.</div>
                 ) : visibleDevices.map(d => {
                   const isTarget = latestRequest?.device_id === d.id;
                   const postureHealthy = d.metadata?.posture === 'HEALTHY';
                   
                   return (
                   <div 
                     key={d.id} data-node-id={d.id} onClick={() => setSelectedNode(d)}
                     className={`p-3 rounded-xl border cursor-pointer transition-all shadow-lg flex items-center justify-between gap-2 relative ${
                       selectedNode?.id === d.id ? 'ring-2 ring-white border-slate-700 bg-slate-800' : 'border-slate-800 bg-slate-900/50 hover:bg-slate-800'
                     }`}
                   >
                     <div className="flex items-center gap-3 overflow-hidden">
                        <Smartphone className={`w-5 h-5 shrink-0 ${isTarget ? 'text-cyan-400' : 'text-slate-400'}`}/>
                        <div className="flex flex-col overflow-hidden">
                          <div className="text-sm font-bold text-white truncate">{d.label}</div>
                          <div className="text-[10px] text-slate-400 truncate">{postureHealthy ? 'Compliant' : 'Non-Compliant'}</div>
                        </div>
                     </div>
                     <div className={`shrink-0 w-4 h-4 rounded-full flex items-center justify-center ${postureHealthy ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                        {postureHealthy ? <ShieldCheck className="w-3 h-3"/> : <div className="w-1.5 h-1.5 bg-red-400 rounded-full"/>}
                     </div>
                   </div>
                 )})}
               </div>
               
               {/* Column 2: PEP */}
               <div className="flex flex-col gap-4 z-10 w-48 pt-16">
                 <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 border-b border-slate-800 pb-2">ZTNA Gateway</div>
                 <div className="text-[10px] text-slate-500 mb-2">Entry point for all requests</div>
                 {pepNodes.map(p => {
                    return (
                   <div 
                     key={p.id} data-node-id={p.id} onClick={() => setSelectedNode(p)}
                     className={`p-5 rounded-2xl border cursor-pointer transition-all flex flex-col items-center justify-center gap-3 shadow-2xl ${
                       selectedNode?.id === p.id ? 'ring-2 ring-white bg-slate-800' : 'bg-[#0b1120]'
                     } ${pepVisualStatus ? `${pepColorClass} ${pepShadowClass}` : 'border-slate-700'}`}
                   >
                     <div className={`p-3 rounded-xl ${pepBgClass}`}>
                        <ShieldCheck className={`w-10 h-10 ${pepIconColorClass}`}/>
                     </div>
                     <div className="text-center">
                       <div className="text-base font-bold text-white">{p.label}</div>
                       <div className="text-[10px] text-slate-400 mt-1">Policy Enforcement<br/>Point</div>
                       {pepVisualStatus && (
                         <div className={`mt-2 text-[10px] font-bold px-2 py-1 rounded w-full border ${
                           pepVisualStatus === 'ALLOWED' ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' :
                           pepVisualStatus === 'PENDING MFA' ? 'text-amber-400 border-amber-500/30 bg-amber-500/10' :
                           'text-red-400 border-red-500/30 bg-red-500/10'
                         }`}>
                           {pepVisualStatus}
                         </div>
                       )}
                     </div>
                   </div>
                 )})}
               </div>

               {/* Column 3: Risk & PDP */}
               <div className="flex flex-col gap-6 z-10 w-48 border border-slate-800 bg-slate-900/30 rounded-2xl p-4">
                 <div>
                   <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 border-b border-slate-800 pb-2">Security Decision</div>
                   <div className="text-[10px] text-slate-500">Policy Decision Point</div>
                 </div>
                 
                 {riskEngine && (
                   <div 
                     key={riskEngine.id} data-node-id={riskEngine.id} onClick={() => setSelectedNode(riskEngine)}
                     className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center gap-2 shadow-xl ${
                       selectedNode?.id === riskEngine.id ? 'ring-2 ring-white bg-slate-800' : 'bg-[#0b1120] border-slate-700'
                     }`}
                   >
                     <Activity className="w-6 h-6 text-indigo-400"/>
                     <div className="text-sm font-bold text-white text-center">{riskEngine.label}</div>
                     {securityState && (
                        <div className={`text-[10px] font-bold mt-1 px-2 py-1 rounded w-full text-center ${
                          securityState.riskLevel === 'HIGH' ? 'text-red-400' : 
                          securityState.riskLevel === 'MEDIUM' ? 'text-amber-400' : 
                          'text-emerald-400'
                        }`}>
                          Risk Score: {securityState.riskScore}<br/>({securityState.riskLevel})
                        </div>
                     )}
                   </div>
                 )}

                 {pdp && (
                   <div 
                     key={pdp.id} data-node-id={pdp.id} onClick={() => setSelectedNode(pdp)}
                     className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center gap-2 shadow-xl ${
                       selectedNode?.id === pdp.id ? 'ring-2 ring-white bg-slate-800' : 'bg-[#0b1120] border-slate-700'
                     }`}
                   >
                     <Target className="w-6 h-6 text-indigo-400"/>
                     <div className="text-sm font-bold text-white text-center">{pdp.label}</div>
                     <div className="text-[10px] text-slate-400">Decision</div>
                     {securityState && (
                        <div className={`text-xs font-bold mt-1 px-4 py-1.5 rounded-lg w-full text-center border ${
                          securityState.pdpDecision === 'ALLOW' ? 'bg-emerald-950/50 text-emerald-400 border-emerald-500/50' :
                          securityState.pdpDecision === 'MFA_REQUIRED' ? 'bg-amber-950/50 text-amber-400 border-amber-500/50' : 
                          'bg-red-950/50 text-red-400 border-red-500/50'
                        }`}>
                          {securityState.pdpDecision}
                        </div>
                     )}
                   </div>
                 )}
               </div>

               {/* Column 4: Microsegments */}
               <div className="flex flex-col gap-3 z-10 w-48">
                 <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 border-b border-slate-800 pb-2">Microsegmentation</div>
                 <div className="text-[10px] text-slate-500 mb-2">Segment-based access control</div>
                 {segments.map(seg => {
                   const isTargetSegment = securityState?.targetSegment === seg.id;
                   
                   return (
                   <div 
                     key={seg.id} data-node-id={seg.id} onClick={() => setSelectedNode(seg)}
                     className={`p-3 rounded-xl border border-dashed cursor-pointer transition-all flex items-center gap-3 shadow-lg ${
                       selectedNode?.id === seg.id ? 'ring-2 ring-white border-solid bg-slate-800' : 'bg-[#0b1120] border-slate-700'
                     } ${isTargetSegment ? 'border-cyan-500/80 bg-cyan-950/20' : 'opacity-70'}`}
                   >
                     <div className="p-1.5 bg-slate-800/50 rounded-lg text-slate-400 shrink-0">
                       <Network className="w-4 h-4"/>
                     </div>
                     <div className="flex flex-col overflow-hidden">
                       <div className="text-sm font-bold text-white truncate">{seg.label}</div>
                       <div className="text-[10px] text-slate-400">Segment Zone</div>
                     </div>
                   </div>
                 )})}
               </div>
               
               {/* Column 5: Resources */}
               <div className="flex flex-col gap-3 z-10 w-56">
                 <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 border-b border-slate-800 pb-2">Protected Resources</div>
                 <div className="text-[10px] text-slate-500 mb-2">Applications and data</div>
                 {resources.map(r => {
                   const isLatest = latestRequest?.resource_id === r.id;
                   let statusClass = 'border-slate-800 opacity-70 bg-[#0b1120]';
                   let statusText = null;
                   
                   if (isLatest && securityState) {
                     if (securityState.isAllow) {
                       statusClass = 'border-emerald-500 bg-emerald-950/20 opacity-100 shadow-[0_0_15px_rgba(16,185,129,0.15)]';
                       statusText = <span className="text-emerald-400 font-bold uppercase mt-0.5">ACCESS GRANTED</span>;
                     } else if (securityState.isMfa) {
                       statusClass = 'border-amber-500 bg-amber-950/20 opacity-100';
                       statusText = <span className="text-amber-400 font-bold uppercase mt-0.5">PENDING MFA</span>;
                     } else {
                       statusClass = 'border-red-500 bg-red-950/20 opacity-100';
                       statusText = <span className="text-red-400 font-bold uppercase mt-0.5">ACCESS DENIED</span>;
                     }
                   }
                   
                   return (
                   <div 
                     key={r.id} data-node-id={r.id} onClick={() => setSelectedNode(r)}
                     className={`p-3 rounded-xl border cursor-pointer transition-all shadow-lg flex items-center gap-3 relative ${
                       selectedNode?.id === r.id ? 'ring-2 ring-white bg-slate-800 opacity-100' : ''
                     } ${statusClass}`}
                   >
                     <div className={`p-1.5 rounded-lg shrink-0 ${isLatest && securityState?.isAllow ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                       <Server className="w-5 h-5"/>
                     </div>
                     <div className="flex flex-col overflow-hidden">
                       <div className="text-sm font-bold text-white truncate">{r.label}</div>
                       <div className="text-[10px] text-slate-400">Segment: {r.metadata?.segment || 'None'}</div>
                       {statusText && <div className="text-[9px]">{statusText}</div>}
                     </div>
                   </div>
                 )})}
               </div>
               
               {/* SVG Edges Overlay */}
               <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
                  <defs>
                    <marker id="arrow-neutral" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill={COLOR_NEUTRAL} />
                    </marker>
                    <marker id="arrow-active" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill="#06b6d4" />
                    </marker>
                    <marker id="arrow-allow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill={COLOR_ALLOW} />
                    </marker>
                    <marker id="arrow-mfa" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill={COLOR_MFA} />
                    </marker>
                    <marker id="arrow-block" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill={COLOR_DENY} />
                    </marker>
                  </defs>
                  
                  {(() => {
                     const paths: any[] = [];
                     
                     // Helper to draw
                     const addPath = (src: string, tgt: string, color: string, dash?: boolean) => {
                         if (nodeRects[src] && nodeRects[tgt]) {
                             paths.push({src, tgt, color, dash});
                         }
                     };

                     if (securityState && latestRequest) {
                         // Only draw the active path if the selected identity is the one in the latest request
                         // If it's a different user, we draw it anyway so they see the global latest request, 
                         // but we might need to ensure the device is visible. 
                         // To match prompt: "However, the active access path should only be drawn for the latest request if its identity/device belongs to the selected identity."
                         
                         const latestUserId = latestRequest.user_id;
                         if (latestUserId === selectedIdentityId) {
                             // 1. User -> Device (cyan)
                             addPath(latestUserId, latestRequest.device_id, '#06b6d4');
                             // 2. Device -> PEP (cyan)
                             addPath(latestRequest.device_id, 'pep_gateway', '#06b6d4');
                             // 3. PEP -> Risk & PEP -> PDP
                             addPath('pep_gateway', 'risk_engine', '#06b6d4');
                             addPath('pep_gateway', 'pdp', '#06b6d4', true);
                             
                             // 4. PDP -> Segment
                             let markerColor = activeColor;
                             addPath('pdp', securityState.targetSegment, markerColor);
                             
                             // 5. Segment -> Resource
                             // ONLY draw if it actually allowed or MFA (pending)
                             // If it's DENY, the path stops before the resource!
                             if (securityState.isAllow || securityState.isMfa) {
                                 addPath(securityState.targetSegment, latestRequest.resource_id, markerColor);
                             }
                         }
                     }
                     
                     return paths.map((p, idx) => {
                        const srcNode = nodeRects[p.src];
                        const tgtNode = nodeRects[p.tgt];
                        if (!srcNode || !tgtNode) return null;
                        
                        const x1 = srcNode.x + srcNode.w;
                        const y1 = srcNode.y + srcNode.h / 2;
                        const x2 = tgtNode.x;
                        const y2 = tgtNode.y + tgtNode.h / 2;
                        
                        // Smart bezier curve
                        const offset = Math.abs(x2 - x1) * 0.4;
                        const path = `M ${x1} ${y1} C ${x1 + offset} ${y1}, ${x2 - offset} ${y2}, ${x2} ${y2}`;
                        
                        let markerId = "url(#arrow-neutral)";
                        if (p.color === '#06b6d4') markerId = "url(#arrow-active)";
                        else if (p.color === COLOR_ALLOW) markerId = "url(#arrow-allow)";
                        else if (p.color === COLOR_MFA) markerId = "url(#arrow-mfa)";
                        else if (p.color === COLOR_DENY) markerId = "url(#arrow-block)";
                        
                        return (
                            <path 
                               key={`path_${idx}`} 
                               d={path} 
                               fill="none" 
                               stroke={p.color} 
                               strokeWidth={2}
                               strokeDasharray={p.dash ? "4 4" : "none"}
                               markerEnd={markerId}
                            />
                        );
                     });
                  })()}
               </svg>
            </div>
          )}
        </div>
        
        {/* Right Status Sidebar */}
        <div className="w-full xl:w-[320px] shrink-0 flex flex-col gap-6">
          
          {/* Identity Summary Card */}
          <div className="bg-[#0b1120] border border-slate-800 rounded-xl p-5 shadow-xl">
            <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4 border-b border-slate-800 pb-2">
               Selected Identity
            </div>
            {selectedIdentityData ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded-full bg-cyan-900/40 flex items-center justify-center text-cyan-400">
                     <UserIcon className="w-5 h-5"/>
                   </div>
                   <div className="flex flex-col overflow-hidden">
                     <span className="text-base font-bold text-white truncate">{selectedIdentityData.label}</span>
                     <span className="text-[10px] text-slate-400 uppercase tracking-wide truncate">{selectedIdentityData.metadata?.role}</span>
                   </div>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/50">
                   <span className="text-xs text-slate-400">Registered Devices</span>
                   <span className="text-sm font-bold text-white">{visibleDevices.length}</span>
                </div>
              </div>
            ) : (
              <div className="text-sm text-slate-500 italic">No identity selected.</div>
            )}
          </div>

          {/* Latest Request Status Card */}
          <div className="bg-[#0b1120] border border-slate-800 rounded-xl p-5 shadow-xl">
             <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4 border-b border-slate-800 pb-2">
               Latest Access Request
             </div>
             
             {!latestRequest || !securityState ? (
                <div className="text-sm text-slate-500 italic">No access request yet</div>
             ) : (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex flex-col">
                       <span className="text-[10px] text-slate-500 uppercase">Identity</span>
                       <span className="text-sm font-bold text-white truncate">{allUsers.find(u => u.id === latestRequest.user_id)?.label || 'Unknown'}</span>
                    </div>
                    <div className="flex flex-col">
                       <span className="text-[10px] text-slate-500 uppercase">Device</span>
                       <span className="text-sm font-bold text-white truncate">{allDevices.find(d => d.id === latestRequest.device_id)?.label || 'Unknown'}</span>
                    </div>
                    <div className="flex flex-col">
                       <span className="text-[10px] text-slate-500 uppercase">Target</span>
                       <span className="text-sm font-bold text-white truncate">{resources.find(r => r.id === latestRequest.resource_id)?.label || 'Unknown'}</span>
                    </div>
                    {latestRequest.timestamp && (
                      <div className="flex flex-col">
                         <span className="text-[10px] text-slate-500 uppercase">Time</span>
                         <span className="text-xs text-slate-300 truncate">{latestRequest.timestamp}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="border-t border-slate-800 pt-4 flex flex-col gap-2">
                     <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-400">Risk Score</span>
                        <span className={`text-xs font-bold ${securityState.riskLevel === 'HIGH' ? 'text-red-400' : securityState.riskLevel === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'}`}>
                          {securityState.riskLevel} - {securityState.riskScore}
                        </span>
                     </div>
                     <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-400">PDP Decision</span>
                        <span className={`text-xs font-bold ${securityState.pdpDecision === 'ALLOW' ? 'text-emerald-400' : securityState.pdpDecision === 'MFA_REQUIRED' ? 'text-amber-400' : 'text-red-400'}`}>
                           {securityState.pdpDecision}
                        </span>
                     </div>
                     <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-400">PEP Enforcement</span>
                        <span className={`text-xs font-bold ${securityState.pepState === 'ALLOWED' ? 'text-emerald-400' : securityState.pepState === 'PENDING MFA' ? 'text-amber-400' : 'text-red-400'}`}>
                           {securityState.pepState}
                        </span>
                     </div>
                     <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-400">Segmentation</span>
                        <span className={`text-xs font-bold ${securityState.segmentationState === 'ALLOWED' ? 'text-emerald-400' : securityState.segmentationState === 'PENDING' ? 'text-amber-400' : 'text-red-400'}`}>
                           {securityState.segmentationState}
                        </span>
                     </div>
                  </div>
                </div>
             )}
          </div>

          {/* Node Details */}
          <div className="bg-[#0b1120] border border-slate-800 rounded-xl p-5 shadow-xl flex-1 min-h-[200px]">
            <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4 border-b border-slate-800 pb-2">
              Node Details
            </div>
            
            {!selectedNode ? (
              <div className="text-sm text-slate-500 italic">
                Click any node for details.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-800">
                  <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">{selectedNode.type}</div>
                  <div className="text-sm font-bold text-white break-words">{selectedNode.label}</div>
                </div>
                
                <div className="space-y-2">
                  {Object.entries(selectedNode.metadata || {}).map(([key, val]) => {
                     let displayVal = String(val);
                     if (val === undefined || val === null || val === '') return null;
                     
                     return (
                      <div key={key} className="flex flex-col overflow-hidden">
                        <span className="text-[10px] text-slate-500 uppercase">{key.replace(/_/g, ' ')}</span>
                        <span className="text-xs font-medium text-slate-200 truncate">{displayVal}</span>
                      </div>
                     );
                  })}
                </div>
              </div>
            )}
          </div>
          
        </div>
      </div>

      {/* Bottom Layout Container */}
      <div className="px-6 flex flex-col gap-4">
        {/* Step-by-Step Access Flow */}
        <div className="bg-[#0b1120] border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col lg:flex-row items-center justify-between gap-4">
           <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest lg:hidden w-full border-b border-slate-800 pb-2">
             Access Flow (Step-by-Step)
           </div>
           
           <div className="flex items-center gap-3 w-full lg:w-auto">
             <div className="w-8 h-8 rounded-full bg-cyan-900/50 text-cyan-400 flex items-center justify-center font-bold text-sm shrink-0 border border-cyan-800">1</div>
             <div className="flex flex-col">
               <span className="text-xs font-bold text-white">Access Request</span>
               <span className="text-[10px] text-slate-400">User + Device + Context</span>
             </div>
           </div>
           
           <ArrowRightCircle className="w-4 h-4 text-slate-600 hidden lg:block shrink-0"/>
           
           <div className="flex items-center gap-3 w-full lg:w-auto">
             <div className="w-8 h-8 rounded-full bg-cyan-900/50 text-cyan-400 flex items-center justify-center font-bold text-sm shrink-0 border border-cyan-800">2</div>
             <div className="flex flex-col">
               <span className="text-xs font-bold text-white">PEP (ZeroGate)</span>
               <span className="text-[10px] text-slate-400">Authenticates and forwards to PDP</span>
             </div>
           </div>
           
           <ArrowRightCircle className="w-4 h-4 text-slate-600 hidden lg:block shrink-0"/>
           
           <div className="flex items-center gap-3 w-full lg:w-auto">
             <div className="w-8 h-8 rounded-full bg-cyan-900/50 text-cyan-400 flex items-center justify-center font-bold text-sm shrink-0 border border-cyan-800">3</div>
             <div className="flex flex-col">
               <span className="text-xs font-bold text-white">Risk & Policy Evaluation</span>
               <span className="text-[10px] text-slate-400">Risk Engine computes score, PDP evaluates</span>
             </div>
           </div>
           
           <ArrowRightCircle className="w-4 h-4 text-slate-600 hidden lg:block shrink-0"/>
           
           <div className="flex items-center gap-3 w-full lg:w-auto">
             <div className="w-8 h-8 rounded-full bg-cyan-900/50 text-cyan-400 flex items-center justify-center font-bold text-sm shrink-0 border border-cyan-800">4</div>
             <div className="flex flex-col">
               <span className="text-xs font-bold text-white">Microsegmentation</span>
               <span className="text-[10px] text-slate-400">Routes to appropriate segment</span>
             </div>
           </div>
           
           <ArrowRightCircle className="w-4 h-4 text-slate-600 hidden lg:block shrink-0"/>
           
           <div className="flex items-center gap-3 w-full lg:w-auto">
             <div className="w-8 h-8 rounded-full bg-cyan-900/50 text-cyan-400 flex items-center justify-center font-bold text-sm shrink-0 border border-cyan-800">5</div>
             <div className="flex flex-col">
               <span className="text-xs font-bold text-white">Resource Access</span>
               <span className="text-[10px] text-slate-400">Grants or denies access</span>
             </div>
           </div>
        </div>

        {/* Lateral Movement Protection Panel */}
        {securityState && (
          <div className="bg-[#0b1120] border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col gap-4">
             <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-2 flex items-center gap-2">
               <ShieldCheck className="w-4 h-4 text-cyan-500"/> Lateral Movement Protection
             </div>
             
             {securityState.isDeny ? (
               <div className="flex flex-col gap-3">
                 <div className="flex items-center gap-2 text-xs font-bold text-red-400 bg-red-950/30 p-2 rounded border border-red-900/50">
                    MICROSEGMENTATION BLOCKED
                 </div>
                 <div className="flex flex-col lg:flex-row items-start lg:items-center gap-4 text-sm text-slate-300 bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                    <div className="flex flex-col">
                      <span className="text-[10px] text-slate-500 uppercase">Source</span>
                      <span className="font-bold text-white">{allUsers.find(u => u.id === latestRequest?.user_id)?.label || latestRequest?.user_id} ({allDevices.find(d => d.id === latestRequest?.device_id)?.label || latestRequest?.device_id})</span>
                    </div>
                    <ArrowRightCircle className="w-4 h-4 text-slate-600 hidden lg:block"/>
                    <div className="flex flex-col text-red-400 font-bold items-center bg-red-950/40 px-3 py-1 rounded">
                      <span>PEP BLOCK</span>
                    </div>
                    <ArrowRightCircle className="w-4 h-4 text-slate-600 hidden lg:block"/>
                    <div className="flex flex-col text-red-400 font-bold items-center bg-red-950/40 px-3 py-1 rounded">
                      <span>MICROSEGMENTATION BLOCKED</span>
                    </div>
                    <ArrowRightCircle className="w-4 h-4 text-slate-600 hidden lg:block"/>
                    <div className="flex flex-col">
                      <span className="text-[10px] text-slate-500 uppercase">Target</span>
                      <span className="font-bold text-white">{resources.find(r => r.id === latestRequest?.resource_id)?.label || latestRequest?.resource_id}</span>
                    </div>
                 </div>
                 <div className="text-xs text-slate-400 italic">
                    Lateral movement prevented by ZeroGate enforcement. Reason: {latestRequest?.reason || 'Unauthorized access attempt'}
                 </div>
               </div>
             ) : (
               <div className="flex items-center gap-2 text-sm text-emerald-400 bg-emerald-950/20 p-3 rounded-lg border border-emerald-900/30">
                  <ShieldCheck className="w-5 h-5"/> No unauthorized lateral movement detected.
               </div>
             )}
          </div>
        )}

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-6 text-[10px] uppercase font-bold text-slate-500 bg-[#0b1120] border border-slate-800 rounded-xl p-3 px-5">
           <span className="text-slate-400">Legend</span>
           <div className="flex items-center gap-2"><div className="w-6 h-0.5 bg-cyan-400"></div> Request Flow</div>
           <div className="flex items-center gap-2"><div className="w-6 h-0.5 bg-emerald-500"></div> Access Granted</div>
           <div className="flex items-center gap-2"><div className="w-6 h-0.5 bg-amber-500"></div> MFA Required</div>
           <div className="flex items-center gap-2"><div className="w-6 h-0.5 bg-red-500"></div> Access Denied</div>
           <div className="flex items-center gap-2"><div className="w-6 h-0.5 border-t border-dashed border-cyan-400"></div> Policy Evaluation</div>
           <div className="flex items-center gap-2"><div className="w-4 h-4 border border-dashed border-slate-500 rounded-sm"></div> Segment Zone</div>
        </div>
      </div>

    </div>
  );
}
