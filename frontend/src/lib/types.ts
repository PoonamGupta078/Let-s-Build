/**
 * Frontend data contracts.
 *
 * Shapes mirror the eventual FastAPI responses (and the report's terminology)
 * so mock data can be swapped for API responses without touching components.
 * Amounts are integer rupees (INR). Timestamps are ISO-8601 strings.
 */

/** Lifecycle of an alert / case in the investigator workflow. */
export type AlertStatus = "NEW" | "INVESTIGATING" | "ESCALATED" | "RESOLVED";

/** Fusion score bands (0-100 risk score). */
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

/** Detector typologies shown on alerts. */
export type DetectionPattern =
  | "Layering"
  | "Round Trip"
  | "Structuring"
  | "Dormancy"
  | "Profile Mismatch";

/** System alert produced by the SEE layer. */
export interface Alert {
  /** e.g. "ALT-9041" */
  id: string;
  /** 0-100 fusion score */
  riskScore: number;
  pattern: DetectionPattern;
  /** Pseudonymised primary account (never a raw account number). */
  accountId: string;
  /** Rupees estimated to be tainted by this alert. */
  taintedAmount: number;
  /** How many accounts the pattern spans. */
  connectedAccounts: number;
  /** ISO-8601 creation time. */
  timestamp: string;
  status: AlertStatus;
  /**
   * Case this alert was escalated into, if any. Optional on purpose: most
   * alerts are not yet cases, so the UI must never imply otherwise.
   */
  caseId?: string;
}

/** Investigation case grouping related alerts. */
export interface Case {
  /** e.g. "CASE-1042" */
  id: string;
  title: string;
  riskScore: number;
  /** Number of connected accounts involved. */
  accounts: number;
  /** Rupees tainted within the case scope. */
  taintedAmount: number;
  status: AlertStatus;
  /** Display name of the assigned investigator. */
  investigator: string;
  /** ISO-8601 of last activity. */
  lastActivity: string;
}

/**
 * One explainable detector finding. These are evidence/finding summaries,
 * never a final investigator decision.
 */
export interface DetectorFinding {
  id: string;
  pattern: DetectionPattern;
  detected: boolean;
  /** 0-100 contribution/severity. */
  contribution: number;
  explanation: string;
}

/** Chronological event for the investigation timeline (future audit trail). */
export interface TimelineEvent {
  id: string;
  /** ISO-8601 */
  timestamp: string;
  event: string;
  description: string;
}

/** Compact evidence metadata for the evidence preview panel. */
export interface EvidenceSummary {
  linkedTransactions: number;
  detectorFindings: number;
  status: "NOT_STARTED" | "DRAFT" | "READY";
  /** ISO-8601 */
  lastUpdated: string;
}

/** One hop of the money-flow summary (Source → … → Exit). */
export interface MoneyFlowStage {
  label: string;
  amount: number;
  note: string;
}

/** Role of a node in the transaction network. */
export type GraphNodeRole =
  | "SOURCE"
  | "MULE"
  | "INTERMEDIARY"
  | "DESTINATION"
  | "EXIT";

/** A vertex in the investigation transaction network. */
export interface InvestigationGraphNode {
  /** Pseudonymised account id. */
  id: string;
  role: GraphNodeRole;
  risk: RiskLevel;
  /** Total rupees received by this account (inflow). */
  inflow: number;
  /** Total rupees sent by this account (outflow). */
  outflow: number;
  /** Number of transactions this account is party to (in + out). */
  transactions: number;
}

/** A directed transaction between two accounts. */
export interface InvestigationGraphEdge {
  /** Transaction / reference id. */
  id: string;
  source: string;
  target: string;
  amount: number;
  currency: string;
  /** ISO-8601 timestamp. */
  timestamp: string;
}

/** The transaction network for an investigation (graph payload). */
export interface InvestigationGraphData {
  nodes: InvestigationGraphNode[];
  edges: InvestigationGraphEdge[];
}

/**
 * Highlight model applied to the graph after a successful TRACE run: the
 * node/edge ids that belong to the trace result. Traced elements are
 * emphasised; everything else is subdued. Produced by lib/traceMap.ts.
 */
export interface GraphHighlight {
  nodeIds: ReadonlySet<string>;
  edgeIds: ReadonlySet<string>;
}

/** Stages of the investigation workflow bar. */
export type InvestigationStage =
  | "SEE"
  | "TRACE"
  | "CUT"
  | "EVIDENCE"
  | "CLINE"
  | "DECISION";

/**
 * Full investigation workspace payload. API-shaped for GET /api/case;
 * `id` is the case id, or the alert id when the alert has no case yet.
 */
export interface Investigation {
  id: string;
  /** Alert that seeded this investigation, when available. */
  alertId?: string;
  title: string;
  riskScore: number;
  status: AlertStatus;
  primaryAccount: string;
  pattern: DetectionPattern;
  taintedAmount: number;
  accountsInvolved: number;
  transactions: number;
  potentialExits: number;
  investigator: string;
  /** ISO-8601 */
  lastActivity: string;
  findings: DetectorFinding[];
  timeline: TimelineEvent[];
  evidenceSummary: EvidenceSummary;
  moneyFlow: MoneyFlowStage[];
  graph: InvestigationGraphData;
}

/** Dashboard KPI tile. */
export interface Kpi {
  id: string;
  label: string;
  /** Pre-formatted display value, e.g. "₹1.84 Cr". */
  value: string;
  /** Small contextual line, e.g. "+4 vs yesterday". */
  context: string;
}

/** One stage of the fund-flow funnel (visual placeholder for TRACE/CUT). */
export interface FundFlowStage {
  label: string;
  /** Rupees at this stage. */
  amount: number;
  note: string;
}

/** Workflow events shown in the activity feed. */
export type ActivityKind =
  | "alert_created"
  | "case_opened"
  | "trace_completed"
  | "evidence_generated"
  | "plan_updated"
  | "decision_pending";

export interface ActivityEvent {
  id: string;
  kind: ActivityKind;
  title: string;
  detail: string;
  /** ISO-8601 */
  timestamp: string;
  /** "System" or an investigator name. */
  actor: string;
}

/** Header notification entry. */
export interface AppNotification {
  id: string;
  title: string;
  detail: string;
  /** ISO-8601 */
  timestamp: string;
}

/** Signed-in investigator (static demo profile). */
export interface InvestigatorProfile {
  name: string;
  role: string;
  initials: string;
}

/** ---------- Backend API shapes (truthful SEE / TRACE / CUT / graph) ---------- */

/** SEE alert as returned by GET /api/alerts. */
export interface SeeAlert {
  alert_id: string;
  rule_id: string;
  rule_name: string;
  account: string;
  score: number;
  window_start: string;
  window_end: string;
  evidence_txn_ids: string[];
  explanation: string;
  disclaimer: string;
}

export interface GraphNode {
  id: string;
  role?: string | null;
  is_exit: boolean;
}

export interface GraphEdge {
  txn_id: string;
  source: string;
  target: string;
  amount: number;
  ts: string;
  channel?: string | null;
  type?: string | null;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  demo: boolean;
}

export interface TraceStep {
  txn_id: string;
  src: string;
  dst: string;
  ts: string;
  amount: number;
  currency: string;
  tainted_amount: number;
  allocation_ratio: number;
  reason: string;
}

export interface TracePath {
  endpoint: string;
  endpoint_tainted: number;
  currency: string;
  steps: TraceStep[];
  greedy: boolean;
}

export interface TraceData {
  seed_account: string;
  seed_amount: number;
  seed_currency: string;
  tainted_accounts: Record<string, Record<string, number>>;
  exit_taint_by_currency: Record<string, number>;
  paths: TracePath[];
  disclaimer: string;
}

export interface CutRecommendation {
  account: string;
  rank: number | null;
  strategy: string;
  evidence_txn_ids: string[];
  estimated_tainted_blocked: number | null;
  estimated_clean_disrupted: number | null;
  minutes_until_exit: number | null;
  rationale: string;
  currency: string;
}

export interface CutData {
  strategy: string;
  seed_accounts: string[];
  exit_accounts: string[];
  baseline_exit_taint: number;
  total_tainted_blocked: number;
  pct_blocked: number | null;
  recommendations: CutRecommendation[];
  aggregate_clean_held: number | null;
  disclaimer: string;
}

/** Dashboard summary from GET /api/overview. */
export interface OverviewData {
  demo: boolean;
  data_source: string;
  accounts: number;
  transactions: number;
  alerts: number;
  rule_distribution: Record<string, number>;
  exits: number;
  seed_accounts: number;
}

