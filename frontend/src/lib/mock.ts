/**
 * Centralised frontend mock data.
 *
 * Every value here is DEMO DATA — not a backend result. Shapes match
 * src/lib/types.ts so the whole module can later be replaced by API
 * responses (fetch → same interfaces) without touching components.
 * Timestamps are anchored to DEMO_NOW (see lib/format.ts).
 */
import { DEMO_NOW } from "@/lib/format";
import type {
  ActivityEvent,
  Alert,
  AppNotification,
  Case,
  FundFlowStage,
  InvestigatorProfile,
  Kpi,
} from "@/lib/types";

const NOW = Date.parse(DEMO_NOW);
/** ISO timestamp `minutes` before the pinned demo clock. */
const ago = (minutes: number): string =>
  new Date(NOW - minutes * 60_000).toISOString();

export const demoKpis: Kpi[] = [
  {
    id: "active-alerts",
    label: "Active Alerts",
    value: "27",
    context: "+4 vs yesterday",
  },
  {
    id: "high-risk-cases",
    label: "High Risk Cases",
    value: "6",
    context: "2 escalated today",
  },
  {
    id: "tainted-traced",
    label: "Tainted Funds Traced",
    value: "₹1.84 Cr",
    context: "+₹12.4L in last 24h",
  },
  {
    id: "pending-decisions",
    label: "Pending Decisions",
    value: "9",
    context: "3 due today",
  },
];

/**
 * Full alert queue — 27 demo alerts, API-shaped for the future
 * GET /api/alerts. Display order is applied by lib/alertQuery.ts.
 */
export const alerts: Alert[] = [
  {
    id: "ALT-9041",
    riskScore: 94,
    pattern: "Layering",
    accountId: "acct_7f3a9c",
    taintedAmount: 4_820_000,
    connectedAccounts: 14,
    timestamp: ago(12),
    status: "NEW",
    caseId: "CASE-1042",
  },
  {
    id: "ALT-9038",
    riskScore: 88,
    pattern: "Round Trip",
    accountId: "acct_2b9d41",
    taintedAmount: 3_175_000,
    connectedAccounts: 9,
    timestamp: ago(46),
    status: "INVESTIGATING",
    caseId: "CASE-1039",
  },
  {
    id: "ALT-9033",
    riskScore: 82,
    pattern: "Structuring",
    accountId: "acct_5c1e08",
    taintedAmount: 1_840_000,
    connectedAccounts: 22,
    timestamp: ago(64),
    status: "ESCALATED",
    caseId: "CASE-1035",
  },
  {
    id: "ALT-9029",
    riskScore: 76,
    pattern: "Dormancy",
    accountId: "acct_9a4f77",
    taintedAmount: 1_205_000,
    connectedAccounts: 5,
    timestamp: ago(120),
    status: "INVESTIGATING",
    caseId: "CASE-1031",
  },
  {
    id: "ALT-9024",
    riskScore: 71,
    pattern: "Profile Mismatch",
    accountId: "acct_3d8b62",
    taintedAmount: 960_000,
    connectedAccounts: 7,
    timestamp: ago(180),
    status: "NEW",
  },
  {
    id: "ALT-9018",
    riskScore: 64,
    pattern: "Layering",
    accountId: "acct_6e2c15",
    taintedAmount: 525_000,
    connectedAccounts: 11,
    timestamp: ago(300),
    status: "RESOLVED",
  },
  {
    id: "ALT-9016",
    riskScore: 73,
    pattern: "Layering",
    accountId: "acct_8d2f64",
    taintedAmount: 760_000,
    connectedAccounts: 10,
    timestamp: ago(330),
    status: "NEW",
  },
  {
    id: "ALT-9013",
    riskScore: 72,
    pattern: "Structuring",
    accountId: "acct_4a7e15",
    taintedAmount: 690_000,
    connectedAccounts: 6,
    timestamp: ago(390),
    status: "INVESTIGATING",
    caseId: "CASE-1035",
  },
  {
    id: "ALT-9011",
    riskScore: 70,
    pattern: "Round Trip",
    accountId: "acct_2c5b93",
    taintedAmount: 645_000,
    connectedAccounts: 8,
    timestamp: ago(420),
    status: "INVESTIGATING",
    caseId: "CASE-1039",
  },
  {
    id: "ALT-9007",
    riskScore: 69,
    pattern: "Dormancy",
    accountId: "acct_6f1e47",
    taintedAmount: 580_000,
    connectedAccounts: 4,
    timestamp: ago(480),
    status: "NEW",
  },
  {
    id: "ALT-9004",
    riskScore: 67,
    pattern: "Profile Mismatch",
    accountId: "acct_3b8d72",
    taintedAmount: 520_000,
    connectedAccounts: 6,
    timestamp: ago(540),
    status: "ESCALATED",
  },
  {
    id: "ALT-9001",
    riskScore: 66,
    pattern: "Layering",
    accountId: "acct_7e4a28",
    taintedAmount: 475_000,
    connectedAccounts: 12,
    timestamp: ago(660),
    status: "INVESTIGATING",
    caseId: "CASE-1042",
  },
  {
    id: "ALT-8997",
    riskScore: 64,
    pattern: "Structuring",
    accountId: "acct_1d9c36",
    taintedAmount: 430_000,
    connectedAccounts: 5,
    timestamp: ago(750),
    status: "RESOLVED",
  },
  {
    id: "ALT-8994",
    riskScore: 62,
    pattern: "Round Trip",
    accountId: "acct_5a3f81",
    taintedAmount: 385_000,
    connectedAccounts: 7,
    timestamp: ago(840),
    status: "NEW",
  },
  {
    id: "ALT-8990",
    riskScore: 60,
    pattern: "Dormancy",
    accountId: "acct_9b6e24",
    taintedAmount: 340_000,
    connectedAccounts: 3,
    timestamp: ago(960),
    status: "INVESTIGATING",
    caseId: "CASE-1031",
  },
  {
    id: "ALT-8986",
    riskScore: 58,
    pattern: "Profile Mismatch",
    accountId: "acct_4f2d69",
    taintedAmount: 300_000,
    connectedAccounts: 5,
    timestamp: ago(1_080),
    status: "NEW",
  },
  {
    id: "ALT-8983",
    riskScore: 56,
    pattern: "Layering",
    accountId: "acct_8a1b57",
    taintedAmount: 265_000,
    connectedAccounts: 9,
    timestamp: ago(1_200),
    status: "ESCALATED",
  },
  {
    id: "ALT-8979",
    riskScore: 54,
    pattern: "Structuring",
    accountId: "acct_2e7c43",
    taintedAmount: 230_000,
    connectedAccounts: 4,
    timestamp: ago(1_380),
    status: "RESOLVED",
  },
  {
    id: "ALT-8975",
    riskScore: 52,
    pattern: "Round Trip",
    accountId: "acct_6c4a18",
    taintedAmount: 195_000,
    connectedAccounts: 6,
    timestamp: ago(1_560),
    status: "NEW",
  },
  {
    id: "ALT-8971",
    riskScore: 50,
    pattern: "Dormancy",
    accountId: "acct_1f8d62",
    taintedAmount: 165_000,
    connectedAccounts: 3,
    timestamp: ago(1_740),
    status: "INVESTIGATING",
    caseId: "CASE-1031",
  },
  {
    id: "ALT-8967",
    riskScore: 48,
    pattern: "Profile Mismatch",
    accountId: "acct_7d3e95",
    taintedAmount: 140_000,
    connectedAccounts: 4,
    timestamp: ago(1_980),
    status: "RESOLVED",
  },
  {
    id: "ALT-8962",
    riskScore: 45,
    pattern: "Layering",
    accountId: "acct_3a6f27",
    taintedAmount: 115_000,
    connectedAccounts: 7,
    timestamp: ago(2_280),
    status: "NEW",
  },
  {
    id: "ALT-8958",
    riskScore: 42,
    pattern: "Structuring",
    accountId: "acct_5e9b14",
    taintedAmount: 92_000,
    connectedAccounts: 3,
    timestamp: ago(2_640),
    status: "RESOLVED",
  },
  {
    id: "ALT-8953",
    riskScore: 39,
    pattern: "Round Trip",
    accountId: "acct_8c2a56",
    taintedAmount: 74_000,
    connectedAccounts: 5,
    timestamp: ago(3_000),
    status: "NEW",
  },
  {
    id: "ALT-8949",
    riskScore: 36,
    pattern: "Dormancy",
    accountId: "acct_4b7d31",
    taintedAmount: 56_000,
    connectedAccounts: 2,
    timestamp: ago(3_480),
    status: "RESOLVED",
  },
  {
    id: "ALT-8944",
    riskScore: 33,
    pattern: "Profile Mismatch",
    accountId: "acct_9e1c48",
    taintedAmount: 42_000,
    connectedAccounts: 3,
    timestamp: ago(4_080),
    status: "NEW",
  },
  {
    id: "ALT-8940",
    riskScore: 30,
    pattern: "Layering",
    accountId: "acct_2a5e79",
    taintedAmount: 28_000,
    connectedAccounts: 4,
    timestamp: ago(5_040),
    status: "RESOLVED",
  },
];

/** Dashboard "Priority Alerts" — the six alerts Prompt 1 surfaced, unchanged. */
const PRIORITY_IDS = [
  "ALT-9041",
  "ALT-9038",
  "ALT-9033",
  "ALT-9029",
  "ALT-9024",
  "ALT-9018",
];
export const priorityAlerts: Alert[] = PRIORITY_IDS.flatMap((id) =>
  alerts.filter((alert) => alert.id === id),
);

export const activeCases: Case[] = [
  {
    id: "CASE-1042",
    title: "Layering ring through 14 mule accounts",
    riskScore: 94,
    accounts: 14,
    taintedAmount: 4_820_000,
    status: "ESCALATED",
    investigator: "R. Sharma",
    lastActivity: ago(8),
  },
  {
    id: "CASE-1039",
    title: "Round-trip wash trading across paired accounts",
    riskScore: 87,
    accounts: 9,
    taintedAmount: 3_175_000,
    status: "INVESTIGATING",
    investigator: "A. Menon",
    lastActivity: ago(32),
  },
  {
    id: "CASE-1035",
    title: "Structuring below reporting threshold",
    riskScore: 81,
    accounts: 22,
    taintedAmount: 1_840_000,
    status: "INVESTIGATING",
    investigator: "R. Sharma",
    lastActivity: ago(60),
  },
  {
    id: "CASE-1031",
    title: "Dormant account reactivated for cash-out",
    riskScore: 74,
    accounts: 5,
    taintedAmount: 1_205_000,
    status: "NEW",
    investigator: "Unassigned",
    lastActivity: ago(120),
  },
];

/** Visual placeholder for the future TRACE/CUT analytics pipeline. */
export const fundFlow: FundFlowStage[] = [
  {
    label: "Tainted funds detected",
    amount: 21_000_000,
    note: "Across 6 open cases",
  },
  {
    label: "Funds traced",
    amount: 18_400_000,
    note: "Followed to cash-out edges",
  },
  {
    label: "Potentially interceptable",
    amount: 9_650_000,
    note: "Before accounts exit the network",
  },
];

export const recentActivity: ActivityEvent[] = [
  {
    id: "ACT-01",
    kind: "decision_pending",
    title: "Investigator decision pending",
    detail: "CASE-1042 hold recommendation for 3 accounts awaits approval",
    timestamp: ago(6),
    actor: "System",
  },
  {
    id: "ACT-02",
    kind: "plan_updated",
    title: "Intervention plan updated",
    detail: "CASE-1042 — CUT plan v3: 3 accounts, ₹31.7L potentially interceptable",
    timestamp: ago(21),
    actor: "R. Sharma",
  },
  {
    id: "ACT-03",
    kind: "evidence_generated",
    title: "Evidence generated",
    detail: "CASE-1039 — STR draft with 42 linked txn_ids, SHA-256 recorded",
    timestamp: ago(60),
    actor: "System",
  },
  {
    id: "ACT-04",
    kind: "trace_completed",
    title: "Taint trace completed",
    detail: "CASE-1039 — ₹31.7L traced across 9 connected accounts",
    timestamp: ago(120),
    actor: "A. Menon",
  },
  {
    id: "ACT-05",
    kind: "case_opened",
    title: "Case opened",
    detail: "CASE-1042 — layering ring linking 3 priority alerts",
    timestamp: ago(180),
    actor: "R. Sharma",
  },
  {
    id: "ACT-06",
    kind: "alert_created",
    title: "Alert created",
    detail: "ALT-9041 — Layering, risk 94 on acct_7f3a9c",
    timestamp: ago(300),
    actor: "System",
  },
];

export const notifications: AppNotification[] = [
  {
    id: "NOT-01",
    title: "New high-risk alert",
    detail: "ALT-9041 · risk 94 · Layering",
    timestamp: ago(12),
  },
  {
    id: "NOT-02",
    title: "Decision due today",
    detail: "CASE-1042 hold recommendation awaiting your decision",
    timestamp: ago(21),
  },
  {
    id: "NOT-03",
    title: "Evidence ready",
    detail: "STR draft for CASE-1039 generated",
    timestamp: ago(60),
  },
];

export const demoInvestigator: InvestigatorProfile = {
  name: "R. Sharma",
  role: "Senior Investigator",
  initials: "RS",
};

/** Sidebar badge counts (demo). */
export const navCounts = { alerts: 27, investigations: 6 };
