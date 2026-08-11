import { NextResponse } from "next/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";

async function proxy(method: "GET" | "POST") {
  try {
    const suffix = method === "GET" ? "/api/v1/scans/mag7/latest" : "/api/v1/scans/mag7";
    const response = await fetch(`${backendBaseUrl}${suffix}`, { method, cache: "no-store", headers: { Accept: "application/json" } });
    return NextResponse.json(await response.json(), { status: response.status, headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json(method === "GET" ? { scan: null, results: [] } : { detail: "Backend unavailable" }, { status: method === "GET" ? 200 : 503 });
  }
}

export async function GET() { return proxy("GET"); }
export async function POST() { return proxy("POST"); }
