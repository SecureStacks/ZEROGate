"use client";

import React, { useEffect, useState } from "react";
import { FileText, ShieldCheck, Plus, Search, CheckCircle, XCircle, Key, Activity, Edit2, Trash2 } from "lucide-react";
import { getPolicies, updatePolicy, deletePolicy, evaluatePolicyPreview, PolicyItem, fetchDemoScenarios, fetchAccessRequests, createPolicy, fetchResources } from "@/lib/api";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<PolicyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [resources, setResources] = useState<any[]>([]);
  
  // Preview
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [previewScenarioId, setPreviewScenarioId] = useState<string>("");
  const [previewResult, setPreviewResult] = useState<any>(null);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newPolicy, setNewPolicy] = useState<Partial<PolicyItem>>({
    name: "",
    description: "",
    priority: 10,
    effect: "ALLOW",
    enabled: true,
    require_managed_device: false,
    require_known_network: false,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    const [pols, scens, reses] = await Promise.all([
      getPolicies(),
      fetchDemoScenarios(),
      fetchResources()
    ]);
    setPolicies(pols);
    setScenarios(scens);
    setResources(reses);
    if (scens.length > 0) setPreviewScenarioId(scens[0].id);
    setLoading(false);
  };

  const handleToggle = async (id: string, current: boolean) => {
    await updatePolicy(id, { enabled: !current });
    fetchData();
  };

  const handleDelete = async (id: string) => {
    if(confirm("Are you sure you want to delete this policy?")) {
      await deletePolicy(id);
      fetchData();
    }
  };

  const handlePreview = async () => {
    if (!previewScenarioId) return;
    
    // We need to fetch access requests to get the ID for the scenario
    try {
      const reqs = await fetchAccessRequests();
      const scen = scenarios.find(s => s.id === previewScenarioId);
      const match = reqs.find((r: any) => r.source_ip === scen?.network.source_ip);
      
      if (match) {
        const result = await evaluatePolicyPreview(match.id);
        setPreviewResult(result);
      }
    } catch(err) {
      console.error(err);
    }
  };

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    const formattedPolicy = {
      ...newPolicy,
      max_risk_score: newPolicy.max_risk_score !== undefined && newPolicy.max_risk_score !== null && newPolicy.max_risk_score.toString() !== "" ? parseInt(newPolicy.max_risk_score as any) : undefined,
      priority: newPolicy.priority ? parseInt(newPolicy.priority as any) : 10,
      required_role: newPolicy.required_role || undefined,
      required_device_posture: newPolicy.required_device_posture || undefined,
      resource_id: newPolicy.resource_id || undefined
    };
    await createPolicy(formattedPolicy);
    setIsModalOpen(false);
    fetchData();
    setNewPolicy({
      name: "",
      description: "",
      priority: 10,
      effect: "ALLOW",
      enabled: true,
      require_managed_device: false,
      require_known_network: false,
    });
  };

  const filtered = policies.filter(p => p.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-indigo-400" />
            Policy Management Console
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Configure dynamic Zero Trust authorization rules, priority rankings, and action triggers.
          </p>
        </div>
        <div className="inline-flex items-center gap-2">
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded shadow-lg transition-colors text-sm font-semibold"
          >
            <Plus className="w-4 h-4" />
            Create Policy
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Policy List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-2 bg-slate-900/50 border border-slate-800 rounded-lg p-2">
            <Search className="w-5 h-5 text-slate-500 ml-2" />
            <input 
              type="text"
              placeholder="Search policies..."
              className="bg-transparent border-none text-white focus:outline-none w-full text-sm"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="space-y-3">
            {loading ? (
              <div className="text-slate-500 text-sm p-4">Loading policies...</div>
            ) : filtered.length === 0 ? (
              <div className="text-slate-500 text-sm p-4">No policies found.</div>
            ) : filtered.map(p => (
              <div key={p.id} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono bg-slate-800 text-slate-400 px-2 py-0.5 rounded">P{p.priority}</span>
                    <h4 className="text-sm font-bold text-white">{p.name}</h4>
                    {!p.enabled && <span className="text-[10px] bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded uppercase">Disabled</span>}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">{p.description}</div>
                  
                  <div className="flex flex-wrap gap-2 mt-3">
                    {p.required_role && <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">Role: {p.required_role}</span>}
                    {p.required_device_posture && <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">Posture: {p.required_device_posture}</span>}
                    {p.require_managed_device && <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">Managed Device</span>}
                    {p.max_risk_score !== null && p.max_risk_score !== undefined && <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">Risk &lt;= {p.max_risk_score}</span>}
                  </div>
                </div>
                
                <div className="flex items-center gap-4 flex-shrink-0">
                  <div className={`px-3 py-1 rounded text-xs font-bold flex items-center gap-1 ${
                    p.effect === 'ALLOW' ? 'bg-emerald-500/20 text-emerald-400' :
                    p.effect === 'MFA_REQUIRED' ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {p.effect === 'ALLOW' ? <CheckCircle className="w-3 h-3"/> :
                     p.effect === 'MFA_REQUIRED' ? <Key className="w-3 h-3"/> : <XCircle className="w-3 h-3"/>}
                    {p.effect}
                  </div>
                  
                  <div className="flex items-center gap-1 border-l border-slate-800 pl-4">
                    <button onClick={() => handleToggle(p.id, p.enabled)} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white" title="Toggle Enable">
                      {p.enabled ? <CheckCircle className="w-4 h-4 text-emerald-500"/> : <XCircle className="w-4 h-4"/>}
                    </button>
                    <button onClick={() => handleDelete(p.id)} className="p-1.5 hover:bg-red-500/20 rounded text-slate-400 hover:text-red-400">
                      <Trash2 className="w-4 h-4"/>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Explainability Preview */}
        <div className="space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
              <Activity className="w-32 h-32 text-indigo-500" />
            </div>
            
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2 relative z-10">
              <ShieldCheck className="w-5 h-5 text-indigo-400" />
              Evaluation Preview
            </h3>
            
            <div className="space-y-4 relative z-10">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Test Scenario</label>
                <select 
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  value={previewScenarioId}
                  onChange={(e) => setPreviewScenarioId(e.target.value)}
                >
                  {scenarios.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              
              <button 
                onClick={handlePreview}
                className="w-full bg-indigo-500 hover:bg-indigo-600 text-white py-2 rounded text-sm font-bold shadow-lg"
              >
                Evaluate Policy
              </button>
              
              {previewResult && (
                <div className="mt-6 border-t border-slate-800 pt-4 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                     <div className="bg-slate-950 p-3 rounded border border-slate-800">
                        <div className="text-xs text-slate-500">RISK SCORE</div>
                        <div className="text-lg font-bold text-white">{previewResult.risk_score}</div>
                     </div>
                     <div className="bg-slate-950 p-3 rounded border border-slate-800">
                        <div className="text-xs text-slate-500">RISK LEVEL</div>
                        <div className={`text-sm font-bold mt-1 ${
                          previewResult.risk_level === 'LOW' ? 'text-emerald-400' :
                          previewResult.risk_level === 'MEDIUM' ? 'text-amber-400' : 'text-red-400'
                        }`}>{previewResult.risk_level}</div>
                     </div>
                  </div>
                  
                  <div className={`p-4 rounded-lg border ${
                    previewResult.decision === 'ALLOW' ? 'bg-emerald-500/10 border-emerald-500/30' :
                    previewResult.decision === 'MFA_REQUIRED' ? 'bg-amber-500/10 border-amber-500/30' :
                    'bg-red-500/10 border-red-500/30'
                  }`}>
                    <div className="text-xs font-bold text-slate-400 mb-1">PDP FINAL DECISION</div>
                    <div className={`text-lg font-black ${
                      previewResult.decision === 'ALLOW' ? 'text-emerald-400' :
                      previewResult.decision === 'MFA_REQUIRED' ? 'text-amber-400' : 'text-red-400'
                    }`}>{previewResult.decision}</div>
                    
                    <div className="mt-2 text-xs text-slate-300">
                      <strong>Matched Policy:</strong> {previewResult.policy_name}
                    </div>
                    <div className="mt-1 text-xs text-slate-400 italic">
                      "{previewResult.reason}"
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-xs font-bold text-slate-500 mb-2">EVALUATION TRACE</div>
                    <div className="space-y-2 max-h-[200px] overflow-y-auto pr-2 custom-scrollbar">
                      {previewResult.evaluated_policies && previewResult.evaluated_policies.map((trace: any, idx: number) => (
                        <div key={idx} className="bg-slate-950 p-2 rounded border border-slate-800 text-xs">
                           <div className="flex justify-between items-start mb-1">
                              <span className="font-semibold text-slate-300">{trace.policy_name}</span>
                              {trace.matched ? (
                                <span className="text-emerald-400 font-bold">MATCH</span>
                              ) : (
                                <span className="text-slate-500">SKIP</span>
                              )}
                           </div>
                           <div className="text-slate-500">{trace.reason}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
      </div>

      {/* Create Policy Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto custom-scrollbar">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center sticky top-0 bg-slate-900 z-10">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-400" />
                Create New Policy
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <XCircle className="w-6 h-6" />
              </button>
            </div>
            
            <form onSubmit={handleCreatePolicy} className="p-6 space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-400 mb-1">Policy Name</label>
                  <input required type="text" value={newPolicy.name} onChange={e => setNewPolicy({...newPolicy, name: e.target.value})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm text-white focus:outline-none focus:border-indigo-500" placeholder="e.g. Developer Git Access" />
                </div>
                
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-slate-400 mb-1">Description</label>
                  <input type="text" value={newPolicy.description} onChange={e => setNewPolicy({...newPolicy, description: e.target.value})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm text-white focus:outline-none focus:border-indigo-500" placeholder="Policy description..." />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Priority (Higher runs first)</label>
                  <input required type="number" min="1" value={newPolicy.priority} onChange={e => setNewPolicy({...newPolicy, priority: parseInt(e.target.value)})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm text-white focus:outline-none focus:border-indigo-500" />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Decision / Effect</label>
                  <select required value={newPolicy.effect} onChange={e => setNewPolicy({...newPolicy, effect: e.target.value})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm text-white focus:outline-none focus:border-indigo-500">
                    <option value="ALLOW">ALLOW</option>
                    <option value="MFA_REQUIRED">MFA_REQUIRED</option>
                    <option value="DENY">DENY</option>
                  </select>
                </div>
              </div>

              <div className="border-t border-slate-800 pt-6">
                <h3 className="text-sm font-bold text-white mb-4">Conditions</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Required Role</label>
                    <select value={newPolicy.required_role || ""} onChange={e => setNewPolicy({...newPolicy, required_role: e.target.value})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm text-white focus:outline-none focus:border-indigo-500">
                      <option value="">Any</option>
                      <option value="Developer">Developer</option>
                      <option value="HR">HR</option>
                      <option value="Finance">Finance</option>
                      <option value="Admin">Admin</option>
                      <option value="Vendor">Vendor</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Resource</label>
                    <select value={newPolicy.resource_id || ""} onChange={e => setNewPolicy({...newPolicy, resource_id: e.target.value})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm text-white focus:outline-none focus:border-indigo-500">
                      <option value="">Any</option>
                      {resources.map(r => (
                        <option key={r.id} value={r.id}>{r.name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Required Device Posture</label>
                    <select value={newPolicy.required_device_posture || ""} onChange={e => setNewPolicy({...newPolicy, required_device_posture: e.target.value})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm text-white focus:outline-none focus:border-indigo-500">
                      <option value="">Any</option>
                      <option value="Healthy">Healthy</option>
                      <option value="Unknown">Unknown</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Maximum Risk Score (0-100)</label>
                    <input type="number" min="0" max="100" value={newPolicy.max_risk_score || ""} onChange={e => setNewPolicy({...newPolicy, max_risk_score: e.target.value ? parseInt(e.target.value) : undefined})} className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-sm text-white focus:outline-none focus:border-indigo-500" placeholder="e.g. 39" />
                  </div>

                  <div className="sm:col-span-2 flex gap-6 mt-2">
                    <label className="flex items-center gap-2 cursor-pointer text-sm text-white">
                      <input type="checkbox" checked={newPolicy.require_managed_device} onChange={e => setNewPolicy({...newPolicy, require_managed_device: e.target.checked})} className="rounded bg-slate-950 border-slate-800 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-slate-900" />
                      Require Managed Device
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer text-sm text-white">
                      <input type="checkbox" checked={newPolicy.enabled} onChange={e => setNewPolicy({...newPolicy, enabled: e.target.checked})} className="rounded bg-slate-950 border-slate-800 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-slate-900" />
                      Enable Policy
                    </label>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-6 border-t border-slate-800">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-sm font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded transition-colors">
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 text-sm font-semibold text-white bg-indigo-500 hover:bg-indigo-600 rounded shadow-lg transition-colors">
                  Create Policy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
