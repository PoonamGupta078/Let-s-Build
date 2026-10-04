"use client";

import React from "react";

interface State {
  hasError: boolean;
  error: Error | null;
}

interface Props {
  children: React.ReactNode;
}

/**
 * Catches render errors in a page subtree and shows a recoverable message
 * instead of a blank screen. Reused at the app root.
 */
export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 p-8 text-center">
          <span className="text-3xl" aria-hidden>⚠️</span>
          <h2 className="text-lg font-semibold text-ink">Something went wrong</h2>
          <p className="max-w-md text-sm text-ink-2">
            {this.state.error?.message ?? "An unexpected error occurred."}
          </p>
          <button
            type="button"
            onClick={() => this.setState({ hasError: false, error: null })}
            className="rounded-lg bg-violet px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet/90"
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
