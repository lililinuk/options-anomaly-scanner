export type ScanProxyMethod = "GET" | "POST";

export type ScanProxyResult = {
  body: unknown;
  status: number;
};

type FetchLike = (input: string, init: RequestInit) => Promise<Response>;

function failedBody(body: unknown, fallback: string): Record<string, unknown> {
  if (body && typeof body === "object" && !Array.isArray(body)) {
    return { ...(body as Record<string, unknown>), run_state: "FAILED" };
  }
  return { detail: fallback, run_state: "FAILED" };
}

export async function proxyScanRequest(
  method: ScanProxyMethod,
  backendBaseUrl: string,
  request: FetchLike = fetch,
): Promise<ScanProxyResult> {
  const suffix = method === "GET" ? "/api/v1/scans/mag7/latest" : "/api/v1/scans/mag7";
  try {
    const response = await request(`${backendBaseUrl}${suffix}`, {
      method,
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      return {
        body: failedBody(null, `Backend returned an invalid response (${response.status})`),
        status: 502,
      };
    }
    return {
      body: response.ok ? body : failedBody(body, `Backend returned ${response.status}`),
      status: response.status,
    };
  } catch {
    return {
      body: failedBody(null, "Backend unavailable"),
      status: 503,
    };
  }
}
