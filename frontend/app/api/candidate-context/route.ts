import { NextRequest, NextResponse } from "next/server";

import { proxyCandidateContext } from "./proxy";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";

async function proxy(request: NextRequest, method: "GET" | "POST") {
  const candidateId = request.nextUrl.searchParams.get("candidateId") ?? "";
  const result = await proxyCandidateContext(method, backendBaseUrl, candidateId);
  return NextResponse.json(result.body, {
    status: result.status,
    headers: { "Cache-Control": "no-store" },
  });
}

export async function GET(request: NextRequest) {
  return proxy(request, "GET");
}

export async function POST(request: NextRequest) {
  return proxy(request, "POST");
}
