import { NextResponse } from "next/server";

import { proxySystemStatus } from "./proxy";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";

export async function GET() {
  const result = await proxySystemStatus(backendBaseUrl);
  return NextResponse.json(result.body, {
    status: result.status,
    headers: { "Cache-Control": "no-store" },
  });
}
