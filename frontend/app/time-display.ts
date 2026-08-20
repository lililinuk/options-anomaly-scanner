const marketFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York",
  year: "numeric",
  month: "short",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  timeZoneName: "short",
});

export type TimestampDisplay = {
  ny: string;
  utc: string;
};

export function timestampDisplay(value: string | null | undefined): TimestampDisplay | null {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return {
    ny: marketFormatter.format(parsed),
    utc: parsed.toISOString().replace(".000Z", "Z"),
  };
}

export function timestampText(value: string | null | undefined): string {
  const formatted = timestampDisplay(value);
  return formatted ? `${formatted.ny} · UTC ${formatted.utc}` : "—";
}
