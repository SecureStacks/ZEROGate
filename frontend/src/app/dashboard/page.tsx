import React from "react";
import { 
  Users, 
  Laptop, 
  Database, 
  Sparkles, 
  Shield, 
  AlertTriangle, 
  CheckCircle,
  Activity,
  XCircle,
  Key
} from "lucide-react";
import Link from "next/link";
import { 
  fetchUsers, 
  fetchDevices, 
  fetchResources, 
  fetchDemoScenarios,
  fetchDashboardSummary,
  fetchRecentActivity
} from "@/lib/api";

export default async function DashboardPage() {
  const [users, devices, resources, scenarios, summary, recentActivity] = await Promise.all([
    fetchUsers(),
    fetchDevices(),
    fetchResources(),
    fetchDemoScenarios(),
    fetchDashboardSummary(),
    fetchRecentActivity(),
  ]);

  const metrics = summary?.metrics || {
    total_users: users.length,
    active_devices: devices.length,
    protected_resources: resources.length,
    total_requests: 0,
    allowed_requests: 0,
    mfa_challenges: 0,
    blocked_requests: 0,
    high_risk_requests: 0
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/60 p-8 border border-slate-800 shadow-xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="relative z-10 max-w-3xl">

          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-3">
            ZeroGate Security Command Center
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Welcome to the Zero Trust Network Access (ZTNA) dashboard. Monitor live access requests, adaptive authentication challenges, and microsegmentation enforcement.
          </p>
        </div>
      </div>

      {/* Security Metrics Overview */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          Security Metrics
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <Users className="w-4 h-4" />
              <span className="text-sm font-medium">Total Users</span>
            </div>
            <div className="text-3xl font-bold text-white">{metrics.total_users}</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
            <div className="flex items-center gap-2 text-emerald-400 mb-2">
              <CheckCircle className="w-4 h-4" />
              <span className="text-sm font-medium">Allowed Requests</span>
            </div>
            <div className="text-3xl font-bold text-white">{metrics.allowed_requests}</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
            <div className="flex items-center gap-2 text-amber-400 mb-2">
              <Key className="w-4 h-4" />
              <span className="text-sm font-medium">MFA Challenges</span>
            </div>
            <div className="text-3xl font-bold text-white">{metrics.mfa_challenges}</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
            <div className="flex items-center gap-2 text-red-400 mb-2">
              <XCircle className="w-4 h-4" />
              <span className="text-sm font-medium">Blocked Requests</span>
            </div>
            <div className="text-3xl font-bold text-white">{metrics.blocked_requests}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-sky-400" />
              Recent Access Activity
            </h2>
            <Link href="/simulator" className="text-sm text-sky-400 hover:text-sky-300">Run Simulator &rarr;</Link>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="pb-3 font-medium">Time</th>
                  <th className="pb-3 font-medium">User</th>
                  <th className="pb-3 font-medium">Resource</th>
                  <th className="pb-3 font-medium">Decision</th>
                  <th className="pb-3 font-medium">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {recentActivity.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      No recent activity. Run the simulator to generate traffic.
                    </td>
                  </tr>
                ) : (
                  recentActivity.map((activity) => (
                    <tr key={activity.id} className="text-slate-300">
                      <td className="py-4 font-mono text-xs text-slate-500">
                        {activity.timestamp ? new Date(activity.timestamp).toLocaleTimeString() : 'N/A'}
                      </td>
                      <td className="py-4 font-medium">{activity.user}</td>
                      <td className="py-4">{activity.resource}</td>
                      <td className="py-4">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          activity.decision === 'ALLOW' ? 'bg-emerald-500/10 text-emerald-400' :
                          activity.decision === 'MFA_REQUIRED' ? 'bg-amber-500/10 text-amber-400' :
                          'bg-red-500/10 text-red-400'
                        }`}>
                          {activity.decision}
                        </span>
                      </td>
                      <td className="py-4">
                        <span className={`flex items-center gap-1.5 text-xs font-bold ${
                          activity.access_granted ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          {activity.access_granted ? <CheckCircle className="w-4 h-4"/> : <XCircle className="w-4 h-4"/>}
                          {activity.access_granted ? 'GRANTED' : 'BLOCKED'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Demo Scenarios Panel */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-400" />
            ZeroGate Simulator
          </h2>
          <p className="text-sm text-slate-400 mb-6">
            Test the PDP and PEP engines interactively. Watch how context, risk, and microsegmentation dynamically block or allow access in real-time.
          </p>
          <div className="space-y-3">
            <Link href="/simulator" className="block w-full py-3 px-4 bg-sky-500 hover:bg-sky-600 text-white font-bold text-center rounded-lg shadow-[0_0_15px_rgba(14,165,233,0.3)] transition-colors">
              Open Access Simulator
            </Link>
          </div>
          
          <div className="mt-8 pt-6 border-t border-slate-800">
             <div className="grid grid-cols-2 gap-4 text-center">
                <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                  <div className="text-xl font-bold text-white">{devices.length}</div>
                  <div className="text-xs text-slate-400 mt-1">Known Devices</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                  <div className="text-xl font-bold text-white">{resources.length}</div>
                  <div className="text-xs text-slate-400 mt-1">Protected Apps</div>
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
