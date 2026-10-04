/**
 * Route + navigation registry shared by the Sidebar and Header so page
 * titles/subtitles never drift between the two.
 */
import {
  Activity,
  Database,
  FileCheck,
  FolderSearch,
  LayoutDashboard,
  Network,
  ScrollText,
  Siren,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** Optional count badge (sidebar). */
  countKey?: "alerts" | "investigations";
}

export interface NavSection {
  title?: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Graph Explorer", href: "/graph", icon: Network },
      {
        label: "Alerts & Cases",
        href: "/alerts",
        icon: Siren,
        countKey: "alerts",
      },
      {
        label: "Investigations",
        href: "/investigations",
        icon: FolderSearch,
        countKey: "investigations",
      },
      { label: "Evidence", href: "/evidence", icon: FileCheck },
    ],
  },
  {
    title: "SYSTEM",
    items: [
      { label: "Data", href: "/data", icon: Database },
      { label: "Model Status", href: "/model-status", icon: Activity },
      { label: "Audit Log", href: "/audit-log", icon: ScrollText },
    ],
  },
];

export interface PageMeta {
  title: string;
  subtitle: string;
}

/** Top-header title/subtitle per route. */
export const PAGE_META: Record<string, PageMeta> = {
  "/dashboard": {
    title: "Investigation Dashboard",
    subtitle: "Monitor suspicious activity, active cases, and fund-flow investigations.",
  },
  "/graph": {
    title: "Graph Explorer",
    subtitle: "Interactive fund-flow network with SEE evidence and TRACE highlighting.",
  },
  "/alerts": {
    title: "Alerts & Cases",
    subtitle: "Review suspicious activity and manage active investigations.",
  },
  "/investigations": {
    title: "Investigations",
    subtitle: "Active fund-flow investigations and case workspaces.",
  },
  "/evidence": {
    title: "Evidence",
    subtitle: "Evidence packs and STR-style reports for filing.",
  },
  "/data": {
    title: "Data",
    subtitle: "Transaction feeds and dataset status.",
  },
  "/model-status": {
    title: "Model Status",
    subtitle: "Detector health and fusion scoring status.",
  },
  "/audit-log": {
    title: "Audit Log",
    subtitle: "Immutable trail of investigator and system actions.",
  },
};

export function pageMeta(pathname: string): PageMeta {
  return (
    PAGE_META[pathname] ?? {
      title: "Fraud Detector",
      subtitle: "Financial crime investigation console.",
    }
  );
}
