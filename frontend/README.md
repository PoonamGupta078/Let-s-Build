# Fraud Detector — Frontend

Next.js 16 (App Router) + TypeScript + Tailwind CSS v4 + lucide-react.

## Run

    npm install
    npm run dev       # http://localhost:3000
    npm run lint      # eslint (flat config)
    npm run build     # production build

## Layout

    src/app/(workspace)/    shell routes: dashboard, alerts, investigations,
                            evidence, data, model-status, audit-log
    src/components/shell/   AppShell, Sidebar, Header
    src/components/ui/      PageHeader, SectionHeader, MetricCard, RiskBadge,
                            StatusBadge, PlaceholderPage
    src/components/dashboard/ AlertTable, InvestigationCard,
                            FundFlowOverview, ActivityTimeline
    src/lib/                types.ts (contracts), mock.ts (demo data),
                            format.ts (INR/time), nav.ts (routes + page meta)

## Conventions

- Design system lives in `src/app/globals.css` (`@theme` tokens: canvas,
  surface, line, ink, accents, risk/status colours). Use tokens, not hexes.
- Mock data is centralised in `src/lib/mock.ts` and shaped like the future
  API responses (`src/lib/types.ts`) — swap the module for fetches later.
- All figures on screen are demo data and labelled as such.
- No vendor/tracex imports — frontend is built from scratch.

