/**
 * Alert queue filtering/sorting — pure functions so the queue component stays
 * declarative and the same logic can back API queries later
 * (GET /api/alerts?risk=…&pattern=…&status=…&sort=…).
 */
import { riskBand } from "@/components/ui/RiskBadge";
import type {
  Alert,
  AlertStatus,
  DetectionPattern,
  RiskLevel,
} from "@/lib/types";

/** Filter option lists (single source for the filter controls). */
export const RISK_LEVELS: RiskLevel[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
export const DETECTION_PATTERNS: DetectionPattern[] = [
  "Layering",
  "Round Trip",
  "Structuring",
  "Dormancy",
  "Profile Mismatch",
];
export const ALERT_STATUSES: AlertStatus[] = [
  "NEW",
  "INVESTIGATING",
  "ESCALATED",
  "RESOLVED",
];

/** Sort modes offered by the queue. */
export type AlertSort = "risk" | "recent" | "amount";

export const SORT_LABELS: Record<AlertSort, string> = {
  risk: "Risk: High → Low",
  recent: "Most Recent",
  amount: "Tainted Amount: High → Low",
};

/** Current queue filter/sort state ("ALL" disables a dimension). */
export interface AlertQuery {
  search: string;
  risk: RiskLevel | "ALL";
  pattern: DetectionPattern | "ALL";
  status: AlertStatus | "ALL";
  sort: AlertSort;
}

export const DEFAULT_ALERT_QUERY: AlertQuery = {
  search: "",
  risk: "ALL",
  pattern: "ALL",
  status: "ALL",
  sort: "risk",
};

/** True when any filter (search, risk, pattern, status) is narrowing the list. */
export function hasActiveFilters(query: AlertQuery): boolean {
  return (
    query.search.trim() !== "" ||
    query.risk !== "ALL" ||
    query.pattern !== "ALL" ||
    query.status !== "ALL"
  );
}

const SORTERS: Record<AlertSort, (a: Alert, b: Alert) => number> = {
  risk: (a, b) => b.riskScore - a.riskScore,
  amount: (a, b) => b.taintedAmount - a.taintedAmount,
  recent: (a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp),
};

/**
 * Filter the alert queue by search text (alert id, account id, case id) and
 * risk/pattern/status, then sort.
 */
export function queryAlerts(alerts: Alert[], query: AlertQuery): Alert[] {
  const term = query.search.trim().toLowerCase();
  const filtered = alerts.filter((alert) => {
    if (query.risk !== "ALL" && riskBand(alert.riskScore) !== query.risk) {
      return false;
    }
    if (query.pattern !== "ALL" && alert.pattern !== query.pattern) {
      return false;
    }
    if (query.status !== "ALL" && alert.status !== query.status) {
      return false;
    }
    if (term === "") return true;
    return (
      alert.id.toLowerCase().includes(term) ||
      alert.accountId.toLowerCase().includes(term) ||
      (alert.caseId?.toLowerCase().includes(term) ?? false)
    );
  });
  return [...filtered].sort(SORTERS[query.sort]);
}