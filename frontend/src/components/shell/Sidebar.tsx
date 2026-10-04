"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Radar, X } from "lucide-react";
import { NAV_SECTIONS } from "@/lib/nav";
import { navCounts } from "@/lib/mock";

interface SidebarProps {
  /** Mobile drawer visibility (controlled by AppShell). */
  open: boolean;
  onClose: () => void;
}

/**
 * Left navigation: brand, primary investigation routes, SYSTEM section.
 * Highlights the active route; collapses into a drawer on small screens.
 */
export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Backdrop (small screens only) */}
      <div
        onClick={onClose}
        className={`fixed inset-0 z-30 bg-black/60 transition-opacity lg:hidden ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        aria-hidden
      />

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-line bg-canvas-deep/95 backdrop-blur-xl transition-transform duration-200 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-label="Primary navigation"
      >
        {/* Brand */}
        <div className="flex h-16 items-center gap-3 border-b border-line px-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-violet/40 bg-violet/15 text-violet">
            <Radar className="h-5 w-5" aria-hidden />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight text-ink">
              Fraud Detector
            </p>
            <p className="text-[10px] uppercase tracking-[0.18em] text-ink-3">
              Investigation Console
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="ml-auto rounded p-1.5 text-ink-2 transition-colors hover:bg-surface-raised hover:text-ink lg:hidden"
            aria-label="Close navigation"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Routes */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.title ?? "primary"} className="mb-6">
              {section.title && (
                <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-ink-3">
                  {section.title}
                </p>
              )}
              <ul className="space-y-1">
                {section.items.map((item) => {
                  const active =
                    pathname === item.href ||
                    pathname.startsWith(`${item.href}/`);
                  const count = item.countKey
                    ? navCounts[item.countKey]
                    : undefined;
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={onClose}
                        aria-current={active ? "page" : undefined}
                        className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                          active
                            ? "bg-violet/15 font-medium text-ink shadow-[inset_2px_0_0_0_var(--color-violet)]"
                            : "text-ink-2 hover:bg-surface-raised hover:text-ink"
                        }`}
                      >
                        <item.icon
                          className={`h-4 w-4 shrink-0 transition-colors ${
                            active
                              ? "text-violet"
                              : "text-ink-3 group-hover:text-violet"
                          }`}
                          aria-hidden
                        />
                        <span className="truncate">{item.label}</span>
                        {count !== undefined && (
                          <span
                            className={`ml-auto rounded px-1.5 py-0.5 text-[10px] font-semibold tabular-nums ${
                              active
                                ? "bg-violet/25 text-ink"
                                : "bg-surface-raised text-ink-3"
                            }`}
                          >
                            {count}
                          </span>
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer note */}
        <div className="border-t border-line px-5 py-3">
          <p className="text-[10px] leading-relaxed text-ink-3">
            Recommendations only — no action here executes a hold. A human
            decides.
          </p>
        </div>
      </aside>
    </>
  );
}
