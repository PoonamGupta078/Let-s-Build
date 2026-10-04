import { AppShell } from "@/components/shell/AppShell";

/**
 * All investigator workspace routes render inside the app shell
 * (sidebar + header). Routes stay clean: /dashboard, /alerts, …
 */
export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
