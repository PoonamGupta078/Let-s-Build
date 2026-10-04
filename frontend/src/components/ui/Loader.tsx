import { Loader2 } from "lucide-react";

/** Full-panel loading spinner with an optional label. */
export function Loader({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-ink-3">
      <Loader2 className="h-5 w-5 animate-spin text-violet" aria-hidden />
      {label}
    </div>
  );
}

/** Generic skeleton block. */
export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded bg-surface-raised ${className}`} />
  );
}

/** Skeleton card used while a dashboard stat tile is loading. */
export function SkeletonCard() {
  return (
    <div className="panel animate-pulse p-5">
      <div className="h-3 w-24 rounded bg-surface-raised" />
      <div className="mt-3 h-6 w-16 rounded bg-surface-raised" />
      <div className="mt-2 h-2 w-32 rounded bg-surface-raised" />
    </div>
  );
}
