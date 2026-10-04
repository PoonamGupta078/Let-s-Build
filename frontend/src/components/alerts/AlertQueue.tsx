"use client";

import { useMemo, useState } from "react";
import { SearchX } from "lucide-react";
import type { Alert } from "@/lib/types";
import {
  DEFAULT_ALERT_QUERY,
  hasActiveFilters,
  queryAlerts,
  type AlertQuery,
} from "@/lib/alertQuery";
import { AlertFilters } from "@/components/alerts/AlertFilters";
import { AlertTable } from "@/components/dashboard/AlertTable";
import { EmptyState } from "@/components/ui/EmptyState";

interface AlertQueueProps {
  alerts: Alert[];
}

/**
 * Interactive alert queue: owns filter/sort state, renders the table, the
 * "Showing X of Y" queue indicator, and the filtered-empty state. Rows open
 * the fixed investigation route /investigations/[id]; data stays in props so
 * this component can later take a fetch result unchanged.
 */
export function AlertQueue({ alerts }: AlertQueueProps) {
  const [query, setQuery] = useState<AlertQuery>(DEFAULT_ALERT_QUERY);
  const clear = () => setQuery(DEFAULT_ALERT_QUERY);
  const visible = useMemo(() => queryAlerts(alerts, query), [alerts, query]);
  const detailHref = (alert: Alert): string => `/investigations/${alert.id}`;

  return (
    <>
      <AlertFilters query={query} onChange={setQuery} onClear={clear} />

      <p
        aria-live="polite"
        className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-3"
      >
        Showing {visible.length} of {alerts.length} alerts
        {hasActiveFilters(query) && " (filtered)"}
      </p>

      {visible.length === 0 ? (
        <EmptyState
          icon={SearchX}
          title="No alerts match your current filters."
          description="Try a different search term, or reset the queue."
          action={
            <button
              type="button"
              onClick={clear}
              className="mt-1 inline-flex h-9 items-center gap-1.5 rounded-lg border border-line bg-glass px-4 text-xs font-medium text-ink transition-colors hover:border-line-strong"
            >
              Clear filters
            </button>
          }
        />
      ) : (
        <AlertTable alerts={visible} detailHref={detailHref} />
      )}
    </>
  );
}