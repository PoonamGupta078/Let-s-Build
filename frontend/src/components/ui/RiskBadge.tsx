import type { RiskLevel } from "@/lib/types";

/** Map a 0-100 fusion score to a display band. */
export function riskBand(score: number): RiskLevel {
  if (score >= 90) return "CRITICAL";
  if (score >= 75) return "HIGH";
  if (score >= 50) return "MEDIUM";
  return "LOW";
}

const BAND_CLASS: Record<RiskLevel, string> = {
  CRITICAL: "text-risk-critical border-risk-critical/40 bg-risk-critical/10",
  HIGH: "text-risk-high border-risk-high/40 bg-risk-high/10",
  MEDIUM: "text-risk-medium border-risk-medium/40 bg-risk-medium/10",
  LOW: "text-risk-low border-risk-low/40 bg-risk-low/10",
};

interface RiskBadgeProps {
  score: number;
  /** Show the band label next to the score (default true). */
  showLabel?: boolean;
}

/** Compact risk score chip: score + band, colour-coded but restrained. */
export function RiskBadge({ score, showLabel = true }: RiskBadgeProps) {
  const band = riskBand(score);
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded border px-1.5 py-0.5 text-xs font-semibold tabular-nums ${BAND_CLASS[band]}`}
      title={`Risk score ${score}/100 — ${band}`}
    >
      {score}
      {showLabel && (
        <span className="text-[10px] font-medium tracking-wide opacity-80">
          {band}
        </span>
      )}
    </span>
  );
}
