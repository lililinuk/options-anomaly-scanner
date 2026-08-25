export type CandidateContextProxyResult = {
  body: unknown;
  status: number;
};

type FetchLike = (input: string, init: RequestInit) => Promise<Response>;

const candidateIdPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function proxyCandidateContext(
  method: "GET" | "POST",
  backendBaseUrl: string,
  candidateId: string,
  request: FetchLike = fetch,
): Promise<CandidateContextProxyResult> {
  if (!candidateIdPattern.test(candidateId)) {
    return { body: { detail: "Invalid ProductCandidate id" }, status: 400 };
  }
  const suffix =
    method === "GET"
      ? `/api/v1/product-candidates/${candidateId}/context`
      : `/api/v1/product-candidates/${candidateId}/context/refresh`;
  try {
    const response = await request(`${backendBaseUrl}${suffix}`, {
      method,
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
