import type { AlertStatus } from "@/lib/types";

const STATUS_CLASS: Record<AlertStatus, string> = {
  NEW: "text-status-new border-status-new/40 bg-status-new/10",
  INVESTIGATING:
    "text-status-investigating border-status-investigating/40 bg-status-investigating/10",
  ESCALATED:
    "text-status-escalated border-status-escalated/40 bg-status-escalated/10",
  RESOLVED:
    "text-status-resolved border-status-resolved/40 bg-status-resolved/10",
};

const STATUS_DOT: Record<AlertStatus, string> = {
  NEW: "bg-status-new",
  INVESTIGATING: "bg-status-investigating",
  ESCALATED: "bg-status-escalated",
  RESOLVED: "bg-status-resolved",
};

/** Status chip: dot + label, semantic colour only. */
export function StatusBadge({ status }: { status: AlertStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded border px-1.5 py-0.5 text-[11px] font-semibold tracking-wide ${STATUS_CLASS[status]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[status]}`} />
      {status}
    </span>
  );
}
