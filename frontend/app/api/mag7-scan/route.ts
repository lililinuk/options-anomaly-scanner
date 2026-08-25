import { NextResponse } from "next/server";

import { proxyScanRequest } from "./proxy";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";

async function proxy(method: "GET" | "POST") {
  const result = await proxyScanRequest(method, backendBaseUrl);
  return NextResponse.json(result.body, {
    status: result.status,
    headers: { "Cache-Control": "no-store" },
  });
}

export async function GET() { return proxy("GET"); }
export async function POST() { return proxy("POST"); }
