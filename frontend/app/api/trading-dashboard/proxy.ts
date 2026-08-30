export type TradingDashboardProxyResult = {
  body: unknown;
  status: number;
};

type FetchLike = (input: string, init: RequestInit) => Promise<Response>;

export async function proxyTradingDashboard(
  backendBaseUrl: string,
  request: FetchLike = fetch,
): Promise<TradingDashboardProxyResult> {
  try {
    const response = await request(`${backendBaseUrl}/api/v1/dashboard/trading`, {
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
    return { body: { detail: "Backend unavailable" }, status: 503 };
  }
}
