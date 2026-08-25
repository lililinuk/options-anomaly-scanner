export type SystemStatusProxyResult = {
  body: unknown;
  status: number;
};

type FetchLike = (input: string, init: RequestInit) => Promise<Response>;

export async function proxySystemStatus(
  backendBaseUrl: string,
  request: FetchLike = fetch,
): Promise<SystemStatusProxyResult> {
  try {
    const response = await request(`${backendBaseUrl}/api/v1/system/status`, {
      method: "GET",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    try {
      return { body: await response.json(), status: response.status };
    } catch {
      return {
        body: { detail: `Backend returned an invalid response (${response.status})` },
        status: 502,
      };
    }
  } catch {
    return {
      body: {
        detail: "Backend unavailable",
        database_status: "unavailable",
      },
      status: 503,
    };
  }
}
