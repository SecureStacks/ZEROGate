const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Centralized fetch wrapper to handle auth/cookies
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const finalOptions = {
    ...options,
    credentials: "include" as RequestCredentials,
  };
  const res = await fetch(url, finalOptions);
  if (res.status === 401) {
    if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
      window.location.href = "/login";
    }
  }
  return res;
}

export async function login(username: string, password: string): Promise<boolean> {
  try {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
      credentials: "include",
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function logout(): Promise<boolean> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/auth/logout`, {
      method: "POST",
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchCurrentUser(): Promise<UserItem | null> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/auth/me`);
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

export interface HealthData {
  status: string;
  database: string;
  version: string;
  environment: string;
  timestamp: string;
}

export async function fetchHealth(): Promise<HealthData> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/health`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`Health check failed with status: ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    return {
      status: "unreachable",
      database: "unknown",
      version: "1.0.0",
      environment: "disconnected",
      timestamp: new Date().toISOString(),
    };
  }
}

export interface UserItem {
  id: string;
  username: string;
  display_name: string;
  email: string;
  role: string;
  department: string;
  status: string;
}

export interface DeviceItem {
  id: string;
  device_name: string;
  device_type: string;
  operating_system: string;
  owner_user_id: string;
  posture_status: string;
  managed: boolean;
  encrypted: boolean;
  compromised: boolean;
}

export interface ResourceItem {
  id: string;
  name: string;
  resource_type: string;
  sensitivity: string;
  network_segment: string;
  host: string;
  port: number;
  protocol: string;
  enabled: boolean;
}

export interface DemoScenarioItem {
  id: string;
  name: string;
  description: string;
  username: string;
  user_role: string;
  device_name: string;
  device_posture: string;
  resource_name: string;
  network: {
    source_ip: string;
    ip_reputation: string;
    network_type: string;
    country: string;
    city: string;
  };
  behavior: {
    unusual_time: boolean;
    unusual_location: boolean;
    unusual_resource: boolean;
    failed_attempts: number;
  };
}

export async function fetchUsers(): Promise<UserItem[]> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/users`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export async function fetchDevices(): Promise<DeviceItem[]> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/devices`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export async function fetchResources(): Promise<ResourceItem[]> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/resources`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export async function fetchDemoScenarios(): Promise<DemoScenarioItem[]> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/demo/scenarios`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export async function createMFAChallenge(access_request_id: string): Promise<any> {
  const res = await fetchWithAuth(`${API_BASE}/api/mfa/challenge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_request_id }),
  });
  if (!res.ok) throw new Error("Failed to create MFA challenge");
  return res.json();
}

export async function verifyMFAChallenge(challenge_id: string, code: string): Promise<any> {
  const res = await fetchWithAuth(`${API_BASE}/api/mfa/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ challenge_id, code }),
  });
  if (!res.ok) throw new Error("Failed to verify MFA challenge");
  return res.json();
}

export interface DashboardSummary {
  metrics: {
    total_users: number;
    active_devices: number;
    protected_resources: number;
    total_requests: number;
    allowed_requests: number;
    mfa_challenges: number;
    blocked_requests: number;
    high_risk_requests: number;
  };
}

export async function fetchDashboardSummary(): Promise<DashboardSummary | null> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/dashboard/summary`, { cache: "no-store" });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

export interface RecentActivityItem {
  id: string;
  timestamp: string;
  user: string;
  resource: string;
  decision: string;
  access_granted: boolean;
  reason: string;
  source_segment: string;
  destination_segment: string;
}

export async function fetchRecentActivity(): Promise<RecentActivityItem[]> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/dashboard/recent-activity`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

// ----------------------------------------------------
// PHASE 8: POLICY, TOPOLOGY, LOGS
// ----------------------------------------------------

export interface PolicyItem {
  id: string;
  name: string;
  description: string;
  effect: string;
  priority: number;
  enabled: boolean;
  required_role?: string;
  required_device_posture?: string;
  require_managed_device: boolean;
  resource_id?: string;
  min_risk_score?: number;
  max_risk_score?: number;
  network_type?: string;
  ip_reputation?: string;
  require_known_network: boolean;
}

export async function getPolicies(): Promise<PolicyItem[]> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/policies`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export async function createPolicy(policy: Partial<PolicyItem>): Promise<PolicyItem | null> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/policies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(policy),
    });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

export async function updatePolicy(id: string, policy: Partial<PolicyItem>): Promise<PolicyItem | null> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/policies/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(policy),
    });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

export async function deletePolicy(id: string): Promise<boolean> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/policies/${id}`, { method: "DELETE" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function evaluatePolicyPreview(access_request_id: string): Promise<any> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/policies/evaluate-preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_request_id }),
    });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

export async function getTopology(): Promise<{ nodes: any[]; edges: any[]; latest_request?: any }> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/topology`, { cache: "no-store" });
    return res.ok ? await res.json() : { nodes: [], edges: [] };
  } catch {
    return { nodes: [], edges: [] };
  }
}

export async function getAuditLogs(params?: { limit?: number; decision?: string; user_id?: string }): Promise<any[]> {
  try {
    let url = `${API_BASE}/api/logs`;
    if (params) {
      const q = new URLSearchParams();
      if (params.limit) q.set("limit", params.limit.toString());
      if (params.decision) q.set("decision", params.decision);
      if (params.user_id) q.set("user_id", params.user_id);
      url += `?${q.toString()}`;
    }
    const res = await fetchWithAuth(url, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export async function getAuditLogDetail(log_id: string): Promise<any> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/logs/${log_id}`, { cache: "no-store" });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}
export async function fetchRiskScenarios(): Promise<any[]> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/risk/scenarios`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export async function fetchAccessRequests(): Promise<any[]> {
  try {
    const res = await fetchWithAuth(`${API_BASE}/api/access-requests`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export async function enforcePEP(access_request_id: string): Promise<any> {
  const res = await fetchWithAuth(`${API_BASE}/api/pep/enforce`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_request_id }),
  });
  if (!res.ok) throw new Error("Failed to enforce PEP");
  return res.json();
}
