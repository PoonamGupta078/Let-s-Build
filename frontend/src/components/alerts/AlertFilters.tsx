"use client";

import { Search, X } from "lucide-react";
import {
  ALERT_STATUSES,
  DETECTION_PATTERNS,
  RISK_LEVELS,
  SORT_LABELS,
  hasActiveFilters,
  type AlertQuery,
  type AlertSort,
} from "@/lib/alertQuery";

interface AlertFiltersProps {
  query: AlertQuery;
  onChange: (next: AlertQuery) => void;
  onClear: () => void;
}

const FIELD =
  "h-9 rounded-lg border border-line bg-glass px-2.5 text-xs text-ink outline-none transition-colors focus:border-line-strong [&>option]:bg-surface";

/**
 * Search + risk/pattern/status/sort controls for the alert queue.
 * Purely controlled — all filtering happens in lib/alertQuery.ts.
 */
export function AlertFilters({ query, onChange, onClear }: AlertFiltersProps) {
  const active = hasActiveFilters(query);

  return (
    <div
      role="search"
      className="panel mb-3 flex flex-col gap-3 p-3 xl:flex-row xl:items-center"
    >
      {/* Search by alert / account / case id */}
      <label className="group relative block w-full xl:max-w-xs">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-3 transition-colors group-focus-within:text-violet"
          aria-hidden
        />
        <input
          type="search"
          value={query.search}
          onChange={(e) => onChange({ ...query, search: e.target.value })}
          placeholder="Search alert, account or case ID…"
          aria-label="Search by alert ID, account ID or case ID"
          className={`${FIELD} w-full pl-8 pr-3 placeholder:text-ink-3`}
        />
      </label>

      <div className="flex flex-wrap items-center gap-2">
        <select
          value={query.risk}
          onChange={(e) =>
            onChange({ ...query, risk: e.target.value as AlertQuery["risk"] })
          }
          aria-label="Filter by risk"
          className={FIELD}
        >
          <option value="ALL">All risk levels</option>
          {RISK_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level.charAt(0) + level.slice(1).toLowerCase()}
            </option>
          ))}
        </select>

        <select
          value={query.pattern}
          onChange={(e) =>
            onChange({
              ...query,
              pattern: e.target.value as AlertQuery["pattern"],
            })
          }
          aria-label="Filter by pattern"
          className={FIELD}
        >
          <option value="ALL">All patterns</option>
          {DETECTION_PATTERNS.map((pattern) => (
            <option key={pattern} value={pattern}>
              {pattern}
            </option>
          ))}
        </select>

        <select
          value={query.status}
          onChange={(e) =>
            onChange({
              ...query,
              status: e.target.value as AlertQuery["status"],
            })
          }
          aria-label="Filter by status"
          className={FIELD}
        >
          <option value="ALL">All statuses</option>
          {ALERT_STATUSES.map((status) => (
            <option key={status} value={status}>
              {status.charAt(0) + status.slice(1).toLowerCase()}
            </option>
          ))}
        </select>

        <select
          value={query.sort}
          onChange={(e) =>
            onChange({ ...query, sort: e.target.value as AlertSort })
          }
          aria-label="Sort alerts"
          className={FIELD}
        >
          {(Object.keys(SORT_LABELS) as AlertSort[]).map((sort) => (
            <option key={sort} value={sort}>
              {SORT_LABELS[sort]}
            </option>
          ))}
        </select>

        {active && (
          <button
            type="button"
            onClick={onClear}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-line px-3 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
          >
            <X className="h-3.5 w-3.5" aria-hidden />
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}