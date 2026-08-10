import { NextResponse } from "next/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";

export async function GET() {
  try {
    const response = await fetch(`${backendBaseUrl}/api/v1/system/status`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }
    return NextResponse.json(await response.json(), {
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json(
      {
        database_status: "unavailable",
        nightwatch_status: "unknown",
        latest_capability_refresh_at: null,
        quota_limit: null,
        quota_remaining: null,
        rate_limit: null,
        rate_limit_remaining: null,
        latest_request_status: null,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  }
}
