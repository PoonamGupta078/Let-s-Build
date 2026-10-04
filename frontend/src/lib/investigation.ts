/**
 * Investigation workspace data — builds the full Investigation payload for a
 * case id or alert id from the centralised mock data. API-shaped for the
 * future GET /api/case; the page only calls getInvestigation(id).
 */
import { DEMO_NOW } from "@/lib/format";
import { activeCases, alerts } from "@/lib/mock";
import type {
  Alert,
  Case,
  DetectionPattern,
  DetectorFinding,
  EvidenceSummary,
  Investigation,
  MoneyFlowStage,
  TimelineEvent,
} from "@/lib/types";

/** Explanation shown for each detector pattern in the findings panel. */
const PATTERN_EXPLANATIONS: Record<DetectionPattern, string> = {
  Layering:
    "Funds split across many small transfers between accounts to obscure their origin.",
  "Round Trip":
    "Funds leave and return to a source-linked account after passing through intermediaries.",
  Structuring:
    "Transfers kept just below reporting thresholds to avoid triggering review.",
  Dormancy:
    "Long-dormant account suddenly reactivated with high-value movement.",
  "Profile Mismatch":
    "Activity inconsistent with the account's declared profile or business type.",
};

const ALL_PATTERNS: DetectionPattern[] = [
  "Layering",
  "Round Trip",
  "Structuring",
  "Dormancy",
  "Profile Mismatch",
];

/** Per-case finding config + volume figures (demo, replaced by GET /api/case). */
const CASE_DETAILS: Record<
  string,
  {
    transactions: number;
    potentialExits: number;
    detected: { pattern: DetectionPattern; contribution: number }[];
  }
> = {
  "CASE-1042": {
    transactions: 214,
    potentialExits: 3,
    detected: [
      { pattern: "Layering", contribution: 92 },
      { pattern: "Structuring", contribution: 61 },
    ],
  },
  "CASE-1039": {
    transactions: 96,
    potentialExits: 2,
    detected: [
      { pattern: "Round Trip", contribution: 88 },
      { pattern: "Layering", contribution: 47 },
    ],
  },
  "CASE-1035": {
    transactions: 142,
    potentialExits: 4,
    detected: [
      { pattern: "Structuring", contribution: 79 },
      { pattern: "Dormancy", contribution: 44 },
    ],
  },
  "CASE-1031": {
    transactions: 58,
    potentialExits: 1,
    detected: [
      { pattern: "Dormancy", contribution: 74 },
      { pattern: "Profile Mismatch", contribution: 52 },
    ],
  },
};

function buildFindings(
  detected: { pattern: DetectionPattern; contribution: number }[],
): DetectorFinding[] {
  const detectedMap = new Map(
    detected.map((d) => [d.pattern, d.contribution]),
  );
  return ALL_PATTERNS.map((pattern) => {
    const contribution = detectedMap.get(pattern);
    return {
      id: `finding-${pattern.toLowerCase().replaceAll(" ", "-")}`,
      pattern,
      detected: contribution !== undefined,
      contribution: contribution ?? 0,
      explanation:
        contribution !== undefined
          ? PATTERN_EXPLANATIONS[pattern]
          : `No ${pattern.toLowerCase()} signal detected in this network.`,
    };
  });
}

function buildTimeline(
  caseId: string,
  seed: Alert | undefined,
  investigator: string,
  lastActivity: string,
): TimelineEvent[] {
  const generatedAt = seed?.timestamp ?? lastActivity;
  return [
    {
      id: `${caseId}-TL-1`,
      timestamp: generatedAt,
      event: "Alert generated",
      description: `System raised ${seed?.id ?? "an alert"} on ${seed?.accountId ?? "the account"}.`,
    },
    {
      id: `${caseId}-TL-2`,
      timestamp: lastActivity,
      event: "Suspicious pattern detected",
      description: "Fusion scoring flagged a network consistent with a known typology.",
    },
    {
      id: `${caseId}-TL-3`,
      timestamp: lastActivity,
      event: "Case opened",
      description: "Investigation workspace created from the alert.",
    },
    {
      id: `${caseId}-TL-4`,
      timestamp: lastActivity,
      event: "Investigator assigned",
      description: `${investigator} took ownership of the case.`,
    },
    {
      id: `${caseId}-TL-5`,
      timestamp: lastActivity,
      event: "Initial evidence collected",
      description: "Linked transactions and detector findings gathered for review.",
    },
    {
      id: `${caseId}-TL-6`,
      timestamp: lastActivity,
      event: "Investigation pending decision",
      description: "Awaiting a human decision on the recommended intervention.",
    },
  ];
}

/** Demo money-flow hops — NOT taint calculations (those come with TRACE). */
function buildMoneyFlow(taintedAmount: number): MoneyFlowStage[] {
  return [
    { label: "Source", amount: taintedAmount, note: "Confirmed-bad seed funds" },
    { label: "Mule Accounts", amount: Math.round(taintedAmount * 0.86), note: "Received and relayed" },
    { label: "Intermediaries", amount: Math.round(taintedAmount * 0.55), note: "Pass-through accounts" },
    { label: "Destination / Exit", amount: Math.round(taintedAmount * 0.31), note: "Cash-out or other-bank" },
  ];
}

function buildEvidenceSummary(
  transactions: number,
  findings: DetectorFinding[],
): EvidenceSummary {
  return {
    linkedTransactions: transactions,
    detectorFindings: findings.filter((f) => f.detected).length,
    status: "DRAFT",
    lastUpdated: new Date(Date.parse(DEMO_NOW) - 18 * 60_000).toISOString(),
  };
}

/** Primary (highest-risk) alert for a case, if any. */
function seedAlertFor(caseId: string): Alert | undefined {
  return alerts
    .filter((a) => a.caseId === caseId)
    .sort((a, b) => b.riskScore - a.riskScore)[0];
}

function buildCaseInvestigation(caseData: Case): Investigation {
  const seed = seedAlertFor(caseData.id);
  const detail = CASE_DETAILS[caseData.id] ?? {
    transactions: 0,
    potentialExits: 0,
    detected: [],
  };
  const findings = buildFindings(detail.detected);
  return {
    id: caseData.id,
    alertId: seed?.id,
    title: caseData.title,
    riskScore: caseData.riskScore,
    status: caseData.status,
    primaryAccount: seed?.accountId ?? "—",
    pattern: seed?.pattern ?? ALL_PATTERNS[0],
    taintedAmount: caseData.taintedAmount,
    accountsInvolved: caseData.accounts,
    transactions: detail.transactions,
    potentialExits: detail.potentialExits,
    investigator: caseData.investigator,
    lastActivity: caseData.lastActivity,
    findings,
    timeline: buildTimeline(
      caseData.id,
      seed,
      caseData.investigator,
      caseData.lastActivity,
    ),
    evidenceSummary: buildEvidenceSummary(detail.transactions, findings),
    moneyFlow: buildMoneyFlow(caseData.taintedAmount),
  };
}

/** Alert without a case → a thin investigation shell (no case id yet). */
function buildAlertInvestigation(alert: Alert): Investigation {
  const findings = buildFindings([
    { pattern: alert.pattern, contribution: alert.riskScore },
  ]);
  const transactions = alert.connectedAccounts * 4;
  return {
    id: alert.id,
    alertId: alert.id,
    title: `${alert.pattern} on ${alert.accountId}`,
    riskScore: alert.riskScore,
    status: alert.status,
    primaryAccount: alert.accountId,
    pattern: alert.pattern,
    taintedAmount: alert.taintedAmount,
    accountsInvolved: alert.connectedAccounts,
    transactions,
    potentialExits: Math.max(1, Math.round(alert.connectedAccounts / 5)),
    investigator: "Unassigned",
    lastActivity: alert.timestamp,
    findings,
    timeline: buildTimeline(alert.id, alert, "Unassigned", alert.timestamp),
    evidenceSummary: buildEvidenceSummary(transactions, findings),
    moneyFlow: buildMoneyFlow(alert.taintedAmount),
  };
}

/**
 * Resolve a case id or alert id to a full investigation workspace payload.
 * Returns undefined for unknown ids (the page shows the 404).
 */
export function getInvestigation(id: string): Investigation | undefined {
  const caseData = activeCases.find((c) => c.id === id);
  if (caseData) return buildCaseInvestigation(caseData);

  const alert = alerts.find((a) => a.id === id);
  if (!alert) return undefined;
  // Alert already has a case → open the case workspace it belongs to.
  if (alert.caseId) {
    const parent = activeCases.find((c) => c.id === alert.caseId);
    if (parent) return buildCaseInvestigation(parent);
  }
  return buildAlertInvestigation(alert);
}
