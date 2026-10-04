"use client";

import { usePathname } from "next/navigation";
import { Bell, Menu, Search } from "lucide-react";
import { pageMeta } from "@/lib/nav";
import { demoInvestigator, notifications } from "@/lib/mock";
import { relativeTime } from "@/lib/format";

interface HeaderProps {
  /** Hamburger handler for the mobile sidebar drawer. */
  onOpenNav: () => void;
  /** Toggle for the notification popover. */
  notificationsOpen: boolean;
  onToggleNotifications: () => void;
  onCloseNotifications: () => void;
}

/**
 * Compact top header: page title + contextual subtitle, investigation
 * search affordance, notification indicator, investigator profile.
 */
export function Header({
  onOpenNav,
  notificationsOpen,
  onToggleNotifications,
  onCloseNotifications,
}: HeaderProps) {
  const pathname = usePathname();
  const meta = pageMeta(pathname);
  const investigator = demoInvestigator;

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-line bg-canvas-deep/85 px-4 backdrop-blur-xl sm:px-6">
      {/* Mobile nav toggle */}
      <button
        type="button"
        onClick={onOpenNav}
        className="rounded-lg border border-line p-2 text-ink-2 transition-colors hover:border-line-strong hover:text-ink lg:hidden"
        aria-label="Open navigation"
      >
        <Menu className="h-4 w-4" />
      </button>

      {/* Page title + subtitle */}
      <div className="min-w-0">
        <h2 className="truncate text-sm font-semibold text-ink sm:text-base">
          {meta.title}
        </h2>
        <p className="hidden truncate text-xs text-ink-3 sm:block">
          {meta.subtitle}
        </p>
      </div>

      <div className="ml-auto flex items-center gap-2 sm:gap-3">
        {/* Search affordance */}
        <label className="group relative hidden md:block">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-3 transition-colors group-focus-within:text-violet"
            aria-hidden
          />
          <input
            type="search"
            placeholder="Search alerts, cases, accounts…"
            className="h-9 w-56 rounded-lg border border-line bg-glass pl-8 pr-3 text-xs text-ink placeholder:text-ink-3 outline-none transition-colors focus:border-line-strong focus:bg-surface lg:w-72"
            aria-label="Search alerts, cases and accounts"
          />
        </label>

        {/* Notifications */}
        <div className="relative">
          {notificationsOpen && (
            <div
              className="fixed inset-0 z-10"
              onMouseDown={onCloseNotifications}
              aria-hidden
            />
          )}
          <button
            type="button"
            onClick={onToggleNotifications}
            className="relative rounded-lg border border-line p-2 text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
            aria-label={`Notifications (${notifications.length} unread)`}
            aria-expanded={notificationsOpen}
          >
            <Bell className="h-4 w-4" />
            <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-magenta px-1 text-[9px] font-bold text-white">
              {notifications.length}
            </span>
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 top-11 z-20 w-72 rounded-lg border border-line bg-surface p-2 shadow-2xl shadow-black/40">
              <p className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-ink-3">
                Notifications
              </p>
              <ul className="space-y-1">
                {notifications.map((n) => (
                  <li
                    key={n.id}
                    className="rounded-md px-2 py-2 transition-colors hover:bg-surface-raised"
                  >
                    <p className="text-xs font-medium text-ink">{n.title}</p>
                    <p className="mt-0.5 text-xs text-ink-2">{n.detail}</p>
                    <p className="mt-0.5 text-[10px] text-ink-3">
                      {relativeTime(n.timestamp)}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Investigator profile */}
        <div className="flex items-center gap-2.5 border-l border-line pl-2 sm:pl-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full border border-violet/40 bg-violet/15 text-xs font-semibold text-violet">
            {investigator.initials}
          </span>
          <div className="hidden leading-tight lg:block">
            <p className="text-xs font-medium text-ink">{investigator.name}</p>
            <p className="text-[10px] text-ink-3">{investigator.role}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
