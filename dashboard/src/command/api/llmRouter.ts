const BASE = '/api/router';

export async function fetchRouterHealth() {
  try {
    const res = await fetch(`${BASE}/health`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchRouterMetrics() {
  try {
    const res = await fetch(`${BASE}/v1/metrics`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
