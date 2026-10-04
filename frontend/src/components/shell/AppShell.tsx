"use client";

import { useState, type ReactNode } from "react";
import { Sidebar } from "@/components/shell/Sidebar";
import { Header } from "@/components/shell/Header";

/**
 * Application shell: fixed sidebar + sticky header + routed page content.
 * The sidebar becomes a drawer below the lg breakpoint.
 */
export function AppShell({ children }: { children: ReactNode }) {
  const [navOpen, setNavOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  return (
    <div className="min-h-screen">
      <Sidebar open={navOpen} onClose={() => setNavOpen(false)} />

      <div className="flex min-h-screen flex-col lg:pl-64">
        <Header
          onOpenNav={() => setNavOpen(true)}
          notificationsOpen={notificationsOpen}
          onToggleNotifications={() => setNotificationsOpen((v) => !v)}
          onCloseNotifications={() => setNotificationsOpen(false)}
        />

        <main className="mx-auto w-full max-w-[1500px] flex-1 px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
