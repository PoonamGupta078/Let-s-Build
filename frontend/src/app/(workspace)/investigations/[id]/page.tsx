import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Construction, FolderSearch, Siren } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { activeCases, alerts } from "@/lib/mock";
import type { AlertStatus } from "@/lib/types";

export const metadata: Metadata = { title: "Investigation" };

interface PageProps {
  params: Promise<{ id: string }>;
}

/**
 * Navigation destination for /investigations/[id] — accepts an alert id or a
 * case id. Only the route contract exists for now; the graph, TRACE and CUT
 * workspace arrives with the next prompt, so this stays a small stub.
 */
export default async function InvestigationRoutePage({ params }: PageProps) {
  const { id } = await params;
  const alert = alerts.find((a) => a.id === id);
  const caseData = activeCases.find((c) => c.id === id);

  if (!alert && !caseData) notFound();

  const isCase = Boolean(caseData);
  const status: AlertStatus | undefined = caseData?.status ?? alert?.status;
  if (!status) notFound();
  const title = caseData?.id ?? alert?.id ?? id;
  const subtitle = caseData
    ? caseData.title
    : `${alert?.pattern} on ${alert?.accountId}`;

  return (
    <>
      <PageHeader
        title={`${isCase ? "Case" : "Alert"} ${title}`}
        subtitle={subtitle}
        meta={
          <>
            {caseData && <RiskBadge score={caseData.riskScore} />}
            <StatusBadge status={status} />
            <Link
              href="/alerts"
              className="inline-flex items-center gap-1.5 rounded border border-line bg-glass px-2 py-1 text-xs text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
              Back to alerts
            </Link>
          </>
        }
      />

      <div className="panel flex max-w-2xl items-start gap-4 p-6">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-violet/25 bg-violet/10 text-violet">
          {isCase ? (
            <FolderSearch className="h-5 w-5" aria-hidden />
          ) : (
            <Siren className="h-5 w-5" aria-hidden />
          )}
        </span>
        <div>
          <p className="text-sm font-medium text-ink">
            The {isCase ? "case workspace" : "alert detail view"} for {title}{" "}
            arrives with the next prompt.
          </p>
          <p className="mt-4 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-3">
            <Construction className="h-3.5 w-3.5" aria-hidden />
            Planned sections
          </p>
          <ul className="mt-2 space-y-1.5">
            {[
              "Transaction graph view (Cytoscape.js)",
              "Taint trail (TRACE) with rupee-level propagation",
              "Hold recommendations (CUT) with impact estimates",
              "Investigator Copilot side panel",
            ].map((item) => (
              <li
                key={item}
                className="flex items-start gap-2 text-xs text-ink-2"
              >
                <span
                  className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-violet/60"
                  aria-hidden
                />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </>
  );
}