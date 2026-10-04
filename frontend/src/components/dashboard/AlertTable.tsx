"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronRight } from "lucide-react";
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
  "Connected Accounts",
  "Time",
  "Status",
] as const;

interface AlertTableProps {
  alerts: Alert[];
  /**
   * Queue mode: when provided, rows navigate here on click and an Action
   * column appears. The Dashboard omits it and keeps its read-only list.
   */
  detailHref?: (alert: Alert) => string;
}

/**
 * Alert table shared by the Dashboard (priority list) and the Alerts &
 * Cases queue (interactive, see `detailHref`).
 */
export function AlertTable({ alerts, detailHref }: AlertTableProps) {
  const router = useRouter();
  const headers = detailHref ? [...HEADERS, "Action"] : HEADERS;

  return (
    <div className="panel overflow-x-auto">
      <table className="w-full min-w-[940px] text-left text-sm">
        <thead>
          <tr className="border-b border-line text-[10px] uppercase tracking-[0.14em] text-ink-3">
            {headers.map((h, i) => (
              <th
                key={h}
                scope="col"
                className={`px-4 py-3 font-medium ${
                  i === 4 || i === 5 || (detailHref && i === headers.length - 1)
                    ? "text-right"
                    : ""
                }`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => {
            const href = detailHref ? detailHref(alert) : "/alerts";
            return (
              <tr
                key={alert.id}
                onClick={
                  detailHref ? () => router.push(href) : undefined
                }
                className={`border-b border-line/60 transition-colors last:border-b-0 hover:bg-surface-raised/60 ${
                  detailHref ? "cursor-pointer" : ""
                }`}
              >
                <td className="px-4 py-3">
                  <Link
                    href={href}
                    onClick={
                      detailHref ? (e) => e.stopPropagation() : undefined
                    }
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
                {detailHref && (
                  <td className="px-4 py-3 text-right">
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-violet">
                      Review
                      <ChevronRight className="h-3.5 w-3.5" aria-hidden />
                    </span>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
