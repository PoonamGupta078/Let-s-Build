"use client";

import { useState } from "react";
import { LoaderCircle, Route, SearchX, TriangleAlert } from "lucide-react";
import type { Investigation, GraphHighlight } from "@/lib/types";
import {
  traceInvestigation,
  TraceBackendUnavailableError,
  TraceRequestError,
  type TraceRequest,
  type TraceResult,
} from "@/lib/api/trace";
import { isTraceEmpty, traceResultToHighlight } from "@/lib/traceMap";
import { formatINR } from "@/lib/format";

type TraceStatus =
  | { kind: "idle" }
  | { kind: "configuring" }
  | { kind: "running" }
  | { kind: "success"; result: TraceResult }
  | { kind: "empty"; result: TraceResult }
  | { kind: "error"; message: string };

interface TraceForm {
  seedAccount: string;
  seedAmount: string;
  seedCurrency: string;
  currencyMode: "per_currency" | "single";
  maxPaths: string;
  exits: string;
}

interface TracePanelProps {
  investigation: Investigation;
  /** Called with the graph highlight after a successful (non-empty) trace. */
  onHighlight: (highlight: GraphHighlight | null) => void;
}

/**
 * TRACE stage UI: "Trace Funds" action, parameter form, execution, and the
 * result / empty / error states. Calls the real TRACE adapter (no fake
 * results); the graph highlight is emitted via onHighlight.
 */
export function TracePanel({ investigation, onHighlight }: TracePanelProps) {
  const [status, setStatus] = useState<TraceStatus>({ kind: "idle" });
  const [form, setForm] = useState<TraceForm>({
    seedAccount: investigation.primaryAccount,
    seedAmount: String(investigation.taintedAmount),
    seedCurrency: "INR",
    currencyMode: "per_currency",
    maxPaths: "10",
    exits: "",
  });

  const set = <K extends keyof TraceForm>(key: K, value: TraceForm[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const openConfig = () => setStatus({ kind: "configuring" });

  const cancel = () => {
    onHighlight(null);
    setStatus({ kind: "idle" });
  };

  const validate = (): string | null => {
    if (form.seedAccount.trim() === "") return "Source account is required.";
    const amount = Number(form.seedAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      return "Amount must be a positive number.";
    }
    if (form.maxPaths.trim() !== "") {
      const mp = Number(form.maxPaths);
      if (!Number.isInteger(mp) || mp < 1) {
        return "Max paths must be an integer ≥ 1.";
      }
    }
    return null;
  };

  const runTrace = async () => {
    const error = validate();
    if (error) {
      setStatus({ kind: "error", message: error });
      return;
    }

    const request: TraceRequest = {
      seedAccount: form.seedAccount.trim(),
      seedAmount: Number(form.seedAmount),
      seedTs: investigation.lastActivity,
      seedCurrency: form.seedCurrency.trim() || undefined,
      currencyMode: form.currencyMode,
      maxPaths: form.maxPaths.trim() === "" ? undefined : Number(form.maxPaths),
      exits:
        form.exits.trim() === ""
          ? undefined
          : form.exits.split(",").map((s) => s.trim()).filter(Boolean),
    };

    setStatus({ kind: "running" });
    onHighlight(null);

    try {
      const result = await traceInvestigation(request);
      if (isTraceEmpty(result)) {
        setStatus({ kind: "empty", result });
      } else {
        setStatus({ kind: "success", result });
        onHighlight(traceResultToHighlight(result));
      }
    } catch (err) {
      if (err instanceof TraceBackendUnavailableError) {
        setStatus({ kind: "error", message: err.message });
      } else if (err instanceof TraceRequestError) {
        setStatus({ kind: "error", message: err.message });
      } else {
        setStatus({
          kind: "error",
          message: "Unable to complete the fund trace. Please retry.",
        });
      }
    }
  };

  const rerun = () => {
    onHighlight(null);
    setStatus({ kind: "configuring" });
  };

  const fieldClass =
    "h-9 w-full rounded-lg border border-line bg-glass px-2.5 text-xs text-ink outline-none transition-colors focus:border-line-strong placeholder:text-ink-3";

  return (
    <div className="panel p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Route className="h-4 w-4 text-magenta" aria-hidden />
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-ink-2">
            Trace
          </h2>
        </div>
        {status.kind === "idle" && (
          <button
            type="button"
            onClick={openConfig}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-violet/50 bg-violet/15 px-4 text-xs font-semibold text-ink transition-colors hover:bg-violet/25"
          >
            Trace Funds
          </button>
        )}
        {(status.kind === "success" || status.kind === "empty") && (
          <button
            type="button"
            onClick={rerun}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-line bg-glass px-4 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
          >
            Re-run TRACE
          </button>
        )}
      </div>

      {status.kind === "idle" && (
        <p className="text-xs text-ink-3">
          Run TRACE to follow the flow of tainted funds from the source account
          through the network.
        </p>
      )}

      {status.kind === "configuring" && (
        <TraceForm
          form={form}
          set={set}
          fieldClass={fieldClass}
          onCancel={cancel}
          onRun={runTrace}
        />
      )}

      {status.kind === "running" && (
        <div className="flex flex-col items-center gap-3 py-8 text-center">
          <LoaderCircle className="h-6 w-6 animate-spin text-magenta" aria-hidden />
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-ink">
              Tracing funds
            </p>
            <p className="mt-1 text-xs text-ink-3">
              Following transaction paths through the network…
            </p>
          </div>
        </div>
      )}

      {status.kind === "error" && (
        <TraceError message={status.message} onRetry={runTrace} onCancel={cancel} />
      )}

      {status.kind === "empty" && <TraceEmpty onRerun={rerun} onCancel={cancel} />}

      {status.kind === "success" && <TraceResults result={status.result} />}
    </div>
  );
}

function TraceForm({
  form,
  set,
  fieldClass,
  onCancel,
  onRun,
}: {
  form: TraceForm;
  set: <K extends keyof TraceForm>(key: K, value: TraceForm[K]) => void;
  fieldClass: string;
  onCancel: () => void;
  onRun: () => void;
}) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            Source account
          </span>
          <input
            type="text"
            value={form.seedAccount}
            onChange={(e) => set("seedAccount", e.target.value)}
            className={fieldClass}
            aria-label="Source account"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            Amount (₹)
          </span>
          <input
            type="number"
            min="0"
            step="1"
            value={form.seedAmount}
            onChange={(e) => set("seedAmount", e.target.value)}
            className={fieldClass}
            aria-label="Amount in rupees"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            Currency
          </span>
          <input
            type="text"
            value={form.seedCurrency}
            onChange={(e) => set("seedCurrency", e.target.value)}
            className={fieldClass}
            aria-label="Currency"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            Currency mode
          </span>
          <select
            value={form.currencyMode}
            onChange={(e) =>
              set("currencyMode", e.target.value as TraceForm["currencyMode"])
            }
            className={`${fieldClass} [&>option]:bg-surface`}
            aria-label="Currency mode"
          >
            <option value="per_currency">Per currency</option>
            <option value="single">Single currency</option>
          </select>
        </label>
        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            Max paths
          </span>
          <input
            type="number"
            min="1"
            step="1"
            value={form.maxPaths}
            onChange={(e) => set("maxPaths", e.target.value)}
            className={fieldClass}
            aria-label="Maximum paths"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            Exit accounts (comma-separated)
          </span>
          <input
            type="text"
            value={form.exits}
            onChange={(e) => set("exits", e.target.value)}
            placeholder="acct_…, acct_…"
            className={fieldClass}
            aria-label="Exit accounts"
          />
        </label>
      </div>

      <div className="flex items-center justify-end gap-2 border-t border-line pt-3">
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex h-9 items-center rounded-lg border border-line bg-glass px-4 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={onRun}
          className="inline-flex h-9 items-center rounded-lg border border-violet/50 bg-violet/15 px-4 text-xs font-semibold text-ink transition-colors hover:bg-violet/25"
        >
          Run Trace
        </button>
      </div>
    </div>
  );
}

function TraceError({
  message,
  onRetry,
  onCancel,
}: {
  message: string;
  onRetry: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-6 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-risk-critical/30 bg-risk-critical/10 text-risk-critical">
        <TriangleAlert className="h-5 w-5" aria-hidden />
      </span>
      <div>
        <p className="text-sm font-semibold uppercase tracking-wider text-ink">
          Trace failed
        </p>
        <p className="mt-1 text-xs text-ink-2">{message}</p>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex h-9 items-center rounded-lg border border-line bg-glass px-4 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
        >
          Retry
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex h-9 items-center rounded-lg border border-line bg-glass px-4 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function TraceEmpty({
  onRerun,
  onCancel,
}: {
  onRerun: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-6 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-line bg-surface text-ink-3">
        <SearchX className="h-5 w-5" aria-hidden />
      </span>
      <div>
        <p className="text-sm font-semibold uppercase tracking-wider text-ink">
          No trace path found
        </p>
        <p className="mt-1 text-xs text-ink-2">
          No qualifying fund-flow path was returned for the selected
          investigation parameters.
        </p>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onRerun}
          className="inline-flex h-9 items-center rounded-lg border border-line bg-glass px-4 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
        >
          Re-run TRACE
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex h-9 items-center rounded-lg border border-line bg-glass px-4 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function TraceResults({ result }: { result: TraceResult }) {
  const accountCount = Object.keys(result.tainted_accounts).length;
  const edgeCount = Object.keys(result.tainted_edges).length;
  const exitCurrencies = Object.keys(result.exit_taint_by_currency);

  return (
    <div className="space-y-4">
      {/* Summary metrics — only fields the TRACE response actually provides */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <ResultStat label="Paths traced" value={`${result.paths.length}`} />
        <ResultStat label="Accounts reached" value={`${accountCount}`} />
        <ResultStat label="Transactions" value={`${edgeCount}`} />
        <ResultStat
          label="Exit taint (currencies)"
          value={exitCurrencies.length > 0 ? `${exitCurrencies.length}` : "—"}
        />
      </div>

      {exitCurrencies.length > 0 && (
        <div className="rounded-lg border border-line/60 bg-surface/40 p-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            Exit taint by currency
          </p>
          <ul className="space-y-1">
            {exitCurrencies.map((currency) => (
              <li
                key={currency}
                className="flex items-center justify-between text-xs"
              >
                <span className="text-ink-2">{currency}</span>
                <span className="font-mono tabular-nums text-ink">
                  {formatINR(result.exit_taint_by_currency[currency])}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Paths */}
      {result.paths.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            Traced paths
          </p>
          {result.paths.map((path, i) => (
            <div
              key={`${path.endpoint}-${i}`}
              className="rounded-lg border border-line/60 bg-surface/40 p-3"
            >
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="font-mono text-xs text-ink-2">
                  → {path.endpoint}
                </span>
                <span className="text-xs tabular-nums text-ink">
                  {formatINR(path.endpoint_tainted)} tainted · {path.currency}
                </span>
              </div>
              <ol className="space-y-1 border-l border-line pl-3">
                {path.steps.map((step) => (
                  <li key={step.txn_id} className="text-[11px] text-ink-2">
                    <span className="font-mono text-violet">{step.txn_id}</span>{" "}
                    {step.src} → {step.dst} ·{" "}
                    <span className="tabular-nums">
                      {formatINR(step.tainted_amount)}
                    </span>{" "}
                    of {formatINR(step.amount)}
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </div>
      )}

      {result.disclaimer && (
        <p className="border-t border-line pt-3 text-[10px] leading-relaxed text-ink-3">
          {result.disclaimer}
        </p>
      )}
    </div>
  );
}

function ResultStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line/60 bg-surface/40 p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-ink-3">
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold tabular-nums text-ink">
        {value}
      </p>
    </div>
  );
}
