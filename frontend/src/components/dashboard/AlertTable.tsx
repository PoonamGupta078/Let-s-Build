"use client";

import Link from "next/link";
import type { Alert } from "@/lib/types";
import { formatINR, relativeTime } from "@/lib/format";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { StatusBadge } from "@/components/ui/StatusBadge";

const HEADERS = [
  "Alert ID",
  "Risk",
  "Pattern",
  "Primary Account",
  "Tainted Amount",
  "Connected",
  "Time",
  "Status",
] as const;

/**
 * Priority alerts table. Rows link to the alerts workspace (the alert
 * detail view arrives with a later prompt).
 */
export function AlertTable({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="panel overflow-x-auto">
      <table className="w-full min-w-[860px] text-left text-sm">
        <thead>
          <tr className="border-b border-line text-[10px] uppercase tracking-[0.14em] text-ink-3">
            {HEADERS.map((h, i) => (
              <th
                key={h}
                scope="col"
                className={`px-4 py-3 font-medium ${i >= 4 && i <= 5 ? "text-right" : ""}`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => (
            <tr
              key={alert.id}
              className="border-b border-line/60 transition-colors last:border-b-0 hover:bg-surface-raised/60"
            >
              <td className="px-4 py-3">
                <Link
                  href="/alerts"
                  className="font-mono text-xs font-medium text-violet transition-colors hover:text-purple hover:underline"
                >
                  {alert.id}
                </Link>
              </td>
              <td className="px-4 py-3">
                <RiskBadge score={alert.riskScore} showLabel={false} />
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-ink-2">
                {alert.pattern}
              </td>
              <td className="px-4 py-3 font-mono text-xs text-ink-2">
                {alert.accountId}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right font-medium tabular-nums text-ink">
                {formatINR(alert.taintedAmount)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums text-ink-2">
                {alert.connectedAccounts}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-xs text-ink-3">
                {relativeTime(alert.timestamp)}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={alert.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
