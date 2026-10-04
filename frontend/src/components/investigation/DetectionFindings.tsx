import { Check, Info, X } from "lucide-react";
import type { DetectorFinding } from "@/lib/types";
import { SectionHeader } from "@/components/ui/SectionHeader";

/**
 * Explainable detector findings. Each row shows detected/not-detected,
 * contribution and a short explanation — evidence summaries, not a final
 * investigator decision.
 */
export function DetectionFindings({
  findings,
}: {
  findings: DetectorFinding[];
}) {
  return (
    <div className="panel p-5">
      <SectionHeader
        title="Detection Findings"
        subtitle="Explainable detector outputs for this network"
      />

      <ul className="space-y-2.5">
        {findings.map((finding) => (
          <li
            key={finding.id}
            className="rounded-lg border border-line/60 bg-surface/40 p-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5">
                <span
                  className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                    finding.detected
                      ? "border-risk-critical/40 bg-risk-critical/10 text-risk-critical"
                      : "border-line bg-surface text-ink-3"
                  }`}
                  aria-hidden
                >
                  {finding.detected ? (
                    <Check className="h-3 w-3" />
                  ) : (
                    <X className="h-3 w-3" />
                  )}
                </span>
                <div>
                  <p className="text-sm font-medium text-ink">
                    {finding.pattern}
                    <span
                      className={`ml-2 text-[10px] font-semibold uppercase tracking-wider ${
                        finding.detected ? "text-risk-critical" : "text-ink-3"
                      }`}
                    >
                      {finding.detected ? "Detected" : "Not detected"}
                    </span>
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-ink-2">
                    {finding.explanation}
                  </p>
                </div>
              </div>
              <span className="shrink-0 text-xs font-semibold tabular-nums text-ink">
                {finding.detected ? `+${finding.contribution}` : "—"}
              </span>
            </div>
          </li>
        ))}
      </ul>

      <p className="mt-4 flex items-start gap-1.5 border-t border-line pt-3 text-[10px] leading-relaxed text-ink-3">
        <Info className="mt-px h-3 w-3 shrink-0" aria-hidden />
        Contributions are detector outputs — an investigator makes the final
        determination.
      </p>
    </div>
  );
}