"use client";

/**
 * SEE alerts from the backend API (/api/alerts), rendered with rule name,
 * score, explanation, and supporting transaction evidence. Data is the
 * synthetic demo case — clearly labelled, not placeholder copy.
 */
import { useEffect, useState } from "react";
import { Loader2, Siren } from "lucide-react";
import { api } from "@/lib/api";
import type { SeeAlert } from "@/lib/types";
import { SectionHeader } from "@/components/ui/SectionHeader";

export function SeeAlertsPanel() {
  const [alerts, setAlerts] = useState<SeeAlert[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .alerts()
      .then(setAlerts)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="panel p-5">
      <SectionHeader
        title="SEE Alerts (synthetic demo)"
        subtitle="Rule-based suspicious-activity alerts served by the backend API"
      />

      {error ? (
        <p className="rounded-lg border border-risk-critical/40 bg-risk-critical/10 p-3 text-sm text-risk-critical">
          {error}
        </p>
      ) : null}

      {!alerts && !error ? (
        <div className="flex items-center gap-2 py-6 text-sm text-ink-3">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          Loading alerts…
        </div>
      ) : null}

      {alerts ? (
        <ul className="space-y-2.5">
          {alerts.map((alert) => (
            <li
              key={alert.alert_id}
              className="rounded-lg border border-line/60 bg-surface/40 p-3"
            >
              <div className="flex items-start gap-2.5">
                <Siren className="mt-0.5 h-4 w-4 shrink-0 text-violet" aria-hidden />
                <div>
                  <p className="text-sm font-medium text-ink">
                    {alert.rule_name}{" "}
                    <span className="text-ink-3">({alert.rule_id})</span>
                    <span className="ml-2 text-[10px] font-semibold uppercase tracking-wider text-magenta">
                      score {alert.score}
                    </span>
                  </p>
                  <p className="mt-0.5 text-xs text-ink-2">
                    account {alert.account}
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-ink-2">
                    {alert.explanation}
                  </p>
                  <p className="mt-1 text-[10px] text-ink-3">
                    evidence: {alert.evidence_txn_ids.join(", ")}
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
