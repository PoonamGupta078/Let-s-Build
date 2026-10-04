/**
 * Display formatting helpers (INR amounts, timestamps).
 *
 * The demo clock (DEMO_NOW) is pinned so relative labels such as "12m ago"
 * render identically during server rendering and on the client — no
 * hydration mismatches, no labels drifting between page loads.
 */

/** Pinned "now" for all demo relative-time labels (IST). */
export const DEMO_NOW = "2026-10-04T14:45:00+05:30";

const INR = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
  minimumFractionDigits: 0,
});

/** Full Indian-grouping rupees, e.g. "₹48,20,000". */
export function formatINR(amount: number): string {
  return INR.format(amount);
}

function trimZeros(value: string): string {
  return value.includes(".") ? value.replace(/\.?0+$/, "") : value;
}

/** Compact rupees for headlines, e.g. "₹1.84 Cr" / "₹96.5 L". */
export function formatINRCompact(amount: number): string {
  const abs = Math.abs(amount);
  if (abs >= 1e7) return `₹${trimZeros((amount / 1e7).toFixed(2))} Cr`;
  if (abs >= 1e5) return `₹${trimZeros((amount / 1e5).toFixed(1))} L`;
  return formatINR(amount);
}

/** Short relative label, e.g. "12m ago", "3h ago", "2d ago". */
export function relativeTime(iso: string, reference: string = DEMO_NOW): string {
  const diffMin = Math.max(
    0,
    Math.round((Date.parse(reference) - Date.parse(iso)) / 60_000),
  );
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const hours = Math.floor(diffMin / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/**
 * Fixed-format timestamp for the demo clock, always in IST regardless of the
 * viewer's timezone: "4 Oct 2026, 14:45 IST". Uses Intl formatToParts (not
 * locale-dependent string templates) so server and client agree byte-for-byte.
 */
export function formatDateTimeIST(iso: string): string {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(new Date(iso));
  const get = (type: Intl.DateTimeFormatPartTypes): string =>
    parts.find((p) => p.type === type)?.value ?? "";
  const day = Number(get("day"));
  return `${day} ${get("month")} ${get("year")}, ${get("hour")}:${get("minute")} IST`;
}
