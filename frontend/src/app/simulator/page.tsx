"use client";

import React, { useEffect, useState } from "react";
import { Sliders, Shield, AlertTriangle, Key, ArrowRight, CheckCircle, XCircle, Activity } from "lucide-react";
import { createMFAChallenge, verifyMFAChallenge, fetchRiskScenarios, fetchAccessRequests, enforcePEP, fetchDemoScenarios } from "@/lib/api";

export default function SimulatorPage() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(null);
  
  // Pipeline State
  const [pipelineState, setPipelineState] = useState<any>(null);
  const [mfaState, setMfaState] = useState<any>(null);

  const [error, setError] = useState<string | null>(null);

  const fetchScenarios = async () => {
    try {
      const demoData = await fetchDemoScenarios();
      const riskData = await fetchRiskScenarios();
      
      if (!demoData || demoData.length === 0) {
        setError("Failed to load scenarios. Please try again later.");
        setLoading(false);
        return;
      }

      // Merge risk data into demo scenarios
      const merged = demoData.map(demo => {
        const riskMatch = riskData.find(r => r.scenario_id === demo.id);
        return {
          ...demo,
          scenario_id: demo.id,
          scenario_name: demo.name,
          risk: riskMatch ? riskMatch.risk : {
             level: "UNKNOWN", score: 0
          }
        };
      });

      setScenarios(merged);
      setError(null);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch scenarios:", err);
      setError("An unexpected error occurred while loading scenarios.");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, []);

  const runScenario = async (scenario: any) => {
    setActiveScenarioId(scenario.scenario_id);
    setPipelineState(null);
    setMfaState(null);
    
    try {
      // 1. Get Access Request ID from the seed (or create one for the demo)
      const reqs = await fetchAccessRequests();
      const match = reqs.find((r: any) => r.source_ip === scenario.network.source_ip);
      
      if (!match) return;

      // 2. Fetch Risk Assessment (already in scenario but let's just use it)
      const risk = scenario.risk;

      // 3. Hit PEP Enforce
      const pepData = await enforcePEP(match.id);
      
      setPipelineState({
        request_id: match.id,
        context: scenario,
        risk: risk,
        pdp: pepData.decision,
        pdpReason: pepData.reason,
        segmentation: pepData.segment_check,
        pep: pepData,
        mfaReEvaluated: false
      });

    } catch(err) {
      console.error(err);
    }
  };

  const handleRequestChallenge = async () => {
    if (!pipelineState) return;
    try {
      const challenge = await createMFAChallenge(pipelineState.request_id);
      setMfaState({ ...challenge, step: "AWAITING_CODE", otpInput: "" });
    } catch (err) {
      console.error("Failed to create challenge", err);
    }
  };

  const handleVerifyOTP = async () => {
    if (!mfaState || !pipelineState) return;
    try {
      const result = await verifyMFAChallenge(mfaState.id, mfaState.otpInput);
      if (result.status === "VERIFIED") {
        setMfaState((prev: any) => ({ ...prev, ...result, step: "VERIFIED" }));
        
        // Re-evaluate PEP
        const pepData = await enforcePEP(pipelineState.request_id);
        
        setPipelineState((prev: any) => ({
          ...prev,
          pdp: pepData.decision,
          pdpReason: pepData.reason,
          segmentation: pepData.segment_check,
          pep: pepData,
          mfaReEvaluated: true
        }));
      } else {
        setMfaState((prev: any) => ({ ...prev, ...result, step: "FAILED" }));
      }
    } catch (err) {
      setMfaState((prev: any) => ({ ...prev, step: "FAILED" }));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Sliders className="w-6 h-6 text-sky-400" />
            Access Simulator
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Simulate and test real-time Zero Trust authorization requests against the PDP engine.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Scenarios & Context */}
        <div className="space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
            <h3 className="font-semibold text-white mb-4">Preset Scenarios</h3>
            {loading ? (
               <p className="text-slate-400 text-sm">Loading scenarios...</p>
            ) : error ? (
               <div className="bg-red-500/10 border border-red-500/50 p-4 rounded-lg">
                 <p className="text-red-400 text-sm font-semibold flex items-center gap-2">
                   <AlertTriangle className="w-4 h-4" />
                   {error}
                 </p>
               </div>
            ) : (
              <div className="space-y-3">
                {scenarios.map((sc, idx) => {
                  let btnLabel = "Run Scenario";
                  if (idx === 0) btnLabel = "Run Normal Access";
                  if (idx === 1) btnLabel = "Run Step-Up Scenario";
                  if (idx === 2) btnLabel = "Run Breach Scenario";
                  if (idx === 3) btnLabel = "Test Lateral Movement";
                  
                  return (
                    <button
                      key={sc.scenario_id}
                      onClick={() => runScenario(sc)}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${
                        activeScenarioId === sc.scenario_id 
                          ? 'bg-sky-500/20 border-sky-500/50 shadow-[0_0_15px_rgba(14,165,233,0.15)]' 
                          : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600'
                      }`}
                    >
                      <div className="font-semibold text-white text-sm mb-1">{sc.scenario_name}</div>
                      <div className="text-xs text-slate-400 mb-3">{sc.description}</div>
                      <div className="text-xs font-bold text-sky-400 bg-sky-500/10 inline-block px-2 py-1 rounded">
                        {btnLabel} &rarr;
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
          
          {pipelineState && (
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 text-sm">
              <h3 className="font-semibold text-white mb-4">Request Context</h3>
              <div className="space-y-4 text-slate-300">
                <div>
                  <div className="text-xs text-slate-500 mb-1">IDENTITY</div>
                  <div>User: <strong className="text-white">{pipelineState.context.username}</strong></div>
                  <div>Role: <strong className="text-white">{pipelineState.context.user_role}</strong></div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">DEVICE</div>
                  <div>Name: <strong className="text-white">{pipelineState.context.device_name}</strong></div>
                  <div>Posture: <strong className="text-white">{pipelineState.context.device_posture}</strong></div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">NETWORK</div>
                  <div>Source IP: <strong className="text-white">{pipelineState.context.network.source_ip}</strong></div>
                  <div>Reputation: <strong className="text-white">{pipelineState.context.network.ip_reputation}</strong></div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">TARGET</div>
                  <div>Resource: <strong className="text-sky-400">{pipelineState.context.resource_name}</strong></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Pipeline */}
        <div className="lg:col-span-2">
          {!pipelineState ? (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px] border border-dashed border-slate-700 rounded-xl bg-slate-900/30 text-slate-500">
              <Shield className="w-12 h-12 mb-3 text-slate-700" />
              <p>Select a scenario to visualize the Zero Trust pipeline.</p>
            </div>
          ) : (
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 relative">
              <h3 className="font-semibold text-white mb-6 flex items-center gap-2">
                <Activity className="w-5 h-5 text-indigo-400" />
                Security Decision Pipeline
              </h3>
              
              <div className="space-y-2 relative">
                {/* Pipeline Line */}
                <div className="absolute left-6 top-10 bottom-10 w-0.5 bg-slate-800 z-0" />
                
                {/* Step 1: Risk Engine */}
                <div className="relative z-10 flex gap-4 bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className={`w-12 h-12 rounded-full flex flex-shrink-0 items-center justify-center font-bold text-lg border-4 border-slate-950 ${
                    pipelineState.risk.level === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                    pipelineState.risk.level === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    {pipelineState.risk.score}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">RISK ENGINE</h4>
                    <div className={`text-xs font-bold mt-1 ${
                      pipelineState.risk.level === 'HIGH' ? 'text-red-400' :
                      pipelineState.risk.level === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {pipelineState.risk.level} RISK
                    </div>
                  </div>
                </div>

                {/* Step 2: PDP */}
                <div className="relative z-10 flex gap-4 bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className={`w-12 h-12 rounded-full flex flex-shrink-0 items-center justify-center border-4 border-slate-950 ${
                    pipelineState.pdp === 'ALLOW' ? 'bg-emerald-500/20 text-emerald-400' :
                    pipelineState.pdp === 'MFA_REQUIRED' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-red-500/20 text-red-400'
                  }`}>
                    {pipelineState.pdp === 'ALLOW' ? <CheckCircle className="w-6 h-6"/> :
                     pipelineState.pdp === 'MFA_REQUIRED' ? <Key className="w-6 h-6"/> :
                     <XCircle className="w-6 h-6"/>}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      POLICY DECISION POINT (PDP)
                      {pipelineState.mfaReEvaluated && <span className="text-[10px] bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded">RE-EVALUATED</span>}
                    </h4>
                    <div className={`text-xs font-bold mt-1 ${
                      pipelineState.pdp === 'ALLOW' ? 'text-emerald-400' :
                      pipelineState.pdp === 'MFA_REQUIRED' ? 'text-amber-400' : 'text-red-400'
                    }`}>
                      {pipelineState.pdp}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">{pipelineState.pdpReason}</div>
                  </div>
                </div>

                {/* MFA Interactive Step */}
                {!pipelineState.mfaReEvaluated && pipelineState.pdp === 'MFA_REQUIRED' && (
                  <div className="relative z-10 flex gap-4 bg-amber-500/5 p-4 rounded-xl border border-amber-500/30 ml-8">
                     <div className="w-8 h-8 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center flex-shrink-0">
                       <Key className="w-4 h-4" />
                     </div>
                     <div className="w-full">
                       <h4 className="text-sm font-bold text-amber-400 mb-2">STEP-UP AUTHENTICATION</h4>
                       {!mfaState ? (
                         <button onClick={handleRequestChallenge} className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded shadow-lg transition-colors">
                           Request Challenge
                         </button>
                       ) : mfaState.step === "AWAITING_CODE" ? (
                         <div className="space-y-2">
                           <div className="text-xs text-slate-300">OTP: <strong className="text-white tracking-widest">{mfaState.demo_otp}</strong></div>
                           <div className="flex gap-2">
                             <input 
                               type="text" 
                               className="bg-slate-900 border border-slate-700 rounded px-3 py-1 text-white focus:outline-none focus:border-sky-500 text-sm"
                               placeholder="000000"
                               value={mfaState.otpInput}
                               onChange={(e) => setMfaState((prev:any) => ({...prev, otpInput: e.target.value}))}
                             />
                             <button onClick={handleVerifyOTP} className="px-4 py-1 bg-sky-500 hover:bg-sky-600 text-white font-bold rounded text-sm">
                               Verify
                             </button>
                           </div>
                         </div>
                       ) : mfaState.step === "FAILED" ? (
                         <div className="text-red-400 text-sm font-bold flex items-center gap-2"><AlertTriangle className="w-4 h-4"/> FAILED</div>
                       ) : (
                         <div className="text-emerald-400 text-sm font-bold flex items-center gap-2"><CheckCircle className="w-4 h-4"/> VERIFIED</div>
                       )}
                     </div>
                  </div>
                )}

                {/* Step 3: Microsegmentation */}
                {pipelineState.pdp === 'ALLOW' && pipelineState.segmentation && (
                  <div className="relative z-10 flex gap-4 bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className={`w-12 h-12 rounded-full flex flex-shrink-0 items-center justify-center border-4 border-slate-950 ${
                      pipelineState.segmentation.allowed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {pipelineState.segmentation.allowed ? <CheckCircle className="w-6 h-6"/> : <XCircle className="w-6 h-6"/>}
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">MICROSEGMENTATION</h4>
                      <div className={`text-xs font-bold mt-1 ${
                        pipelineState.segmentation.allowed ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {pipelineState.segmentation.allowed ? 'ALLOW' : 'DENY'}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        Rule: {pipelineState.pep.segment_check.source_segment || "Unknown"} &rarr; {pipelineState.pep.segment_check.destination_segment || "Unknown"}
                      </div>
                      {!pipelineState.segmentation.allowed && (
                        <div className="text-xs text-red-400 mt-1">{pipelineState.segmentation.reason}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* Final PEP */}
                <div className="relative z-10 flex gap-4 bg-slate-950 p-4 rounded-xl border border-slate-800 mt-6 shadow-xl">
                   <div className={`w-12 h-12 rounded-full flex flex-shrink-0 items-center justify-center border-4 border-slate-950 ${
                      pipelineState.pep.access_granted ? 'bg-emerald-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)]' :
                      pipelineState.pep.decision === 'MFA_REQUIRED' ? 'bg-amber-500 text-white shadow-[0_0_15px_rgba(245,158,11,0.3)]' :
                      'bg-red-500 text-white shadow-[0_0_15px_rgba(239,68,68,0.3)]'
                   }`}>
                     {pipelineState.pep.access_granted ? <CheckCircle className="w-6 h-6"/> :
                      pipelineState.pep.decision === 'MFA_REQUIRED' ? <Key className="w-6 h-6"/> :
                      <XCircle className="w-6 h-6"/>}
                   </div>
                   <div>
                     <h4 className="text-sm font-bold text-white">POLICY ENFORCEMENT POINT (PEP)</h4>
                     <div className={`text-base font-black uppercase mt-1 tracking-wider ${
                        pipelineState.pep.access_granted ? 'text-emerald-400' :
                        pipelineState.pep.decision === 'MFA_REQUIRED' ? 'text-amber-400' :
                        'text-red-400'
                     }`}>
                        {pipelineState.pep.access_granted ? 'ACCESS GRANTED' : 
                         pipelineState.pep.decision === 'MFA_REQUIRED' ? 'STEP-UP REQUIRED' : 'BLOCKED'}
                     </div>
                     <div className="text-xs text-slate-400 mt-1">{pipelineState.pep.reason}</div>
                   </div>
                </div>

              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
