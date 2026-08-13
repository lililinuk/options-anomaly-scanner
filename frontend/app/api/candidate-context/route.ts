import { NextRequest, NextResponse } from "next/server";

const backendBase = process.env.BACKEND_BASE_URL ?? "http://127.0.0.1:8000";
const contractPattern = /^[A-Z0-9]{1,32}$/;

export async function GET(request: NextRequest) {
  const contract = request.nextUrl.searchParams.get("contract") ?? "";
  if (!contractPattern.test(contract)) {
    return NextResponse.json({ detail: "Invalid contract" }, { status: 400 });
  }
  try {
    const response = await fetch(
      `${backendBase}/api/v1/scans/candidates/${encodeURIComponent(contract)}/confirmation`,
      { cache: "no-store" },
    );
    const body = await response.json();
    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json({ detail: "Backend unavailable" }, { status: 503 });
  }
}
