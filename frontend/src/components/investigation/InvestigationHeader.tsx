import Link from "next/link";
import { ArrowLeft, Ellipsis, Flag, LogOut, UserCheck } from "lucide-react";
import type { Investigation } from "@/lib/types";
import { formatDateTimeIST } from "@/lib/format";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { StatusBadge } from "@/components/ui/StatusBadge";

/**
 * Investigation header: case/alert id, title, risk, status, primary account
 * and last activity, plus UI-only action controls (not wired to a backend).
 */
export function InvestigationHeader({
  investigation,
}: {
  investigation: Investigation;
}) {
  const isCase = investigation.id.startsWith("CASE-");

  return (
    <header className="panel mb-6 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        {/* Identity */}
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/alerts"
              className="inline-flex items-center gap-1.5 rounded border border-line bg-glass px-2 py-1 text-xs text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
              Back
            </Link>
            <span className="font-mono text-lg font-semibold tracking-tight text-ink">
              {investigation.id}
            </span>
            {investigation.alertId && investigation.alertId !== investigation.id && (
              <span className="rounded border border-line bg-glass px-1.5 py-0.5 font-mono text-[11px] text-ink-3">
                from {investigation.alertId}
              </span>
            )}
            {!isCase && (
              <span className="rounded border border-violet/40 bg-violet/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-violet">
                No case yet
              </span>
            )}
          </div>

          <h1 className="mt-2 text-xl font-semibold leading-snug tracking-tight text-ink">
            {investigation.title}
          </h1>

          <dl className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs">
            <div className="flex items-center gap-2">
              <dt className="uppercase tracking-wider text-ink-3">Risk</dt>
              <dd>
                <RiskBadge score={investigation.riskScore} />
              </dd>
            </div>
            <div className="flex items-center gap-2">
              <dt className="uppercase tracking-wider text-ink-3">Status</dt>
              <dd>
                <StatusBadge status={investigation.status} />
              </dd>
            </div>
            <div className="flex items-center gap-2">
              <dt className="uppercase tracking-wider text-ink-3">
                Primary account
              </dt>
              <dd className="font-mono text-ink-2">
                {investigation.primaryAccount}
              </dd>
            </div>
            <div className="flex items-center gap-2">
              <dt className="uppercase tracking-wider text-ink-3">
                Last activity
              </dt>
              <dd className="tabular-nums text-ink-2">
                {formatDateTimeIST(investigation.lastActivity)}
              </dd>
            </div>
          </dl>
        </div>

        {/* Actions (UI-only) */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled
            title="Not wired to a backend in this demo"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-line bg-glass px-3 text-xs font-medium text-ink-2 opacity-60"
          >
            <UserCheck className="h-3.5 w-3.5" aria-hidden />
            Assign
          </button>
          <button
            type="button"
            disabled
            title="Not wired to a backend in this demo"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-line bg-glass px-3 text-xs font-medium text-ink-2 opacity-60"
          >
            <Flag className="h-3.5 w-3.5" aria-hidden />
            Escalate
          </button>
          <button
            type="button"
            disabled
            title="Not wired to a backend in this demo"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-line bg-glass px-3 text-xs font-medium text-ink-2 opacity-60"
          >
            <LogOut className="h-3.5 w-3.5" aria-hidden />
            Mark resolved
          </button>
          <button
            type="button"
            disabled
            aria-label="More actions"
            title="Not wired to a backend in this demo"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line bg-glass text-ink-2 opacity-60"
          >
            <Ellipsis className="h-4 w-4" aria-hidden />
          </button>
        </div>
      </div>
    </header>
  );
}