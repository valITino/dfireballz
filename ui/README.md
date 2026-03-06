# DFIReballz UI

React + TypeScript + Tailwind CSS frontend for the DFIReballz digital forensics investigation platform.

## Stack

- React 18 with TypeScript
- Vite build tool
- Tailwind CSS 3 with dark forensic theme
- React Router for navigation
- Axios for API communication
- Lucide React icons

## Development

```bash
npm install
npm run dev
```

The dev server starts on `http://localhost:3000` and proxies API requests to `http://localhost:8800`.

## Build

```bash
npm run build
```

## Docker

```bash
docker build -t dfireballz-ui .
docker run -p 3000:3000 dfireballz-ui
```

## Pages

- **Dashboard** — Active cases grid, quick stats, recent activity, playbook quick-launch
- **New Case** — Case creation form with evidence upload and hash computation
- **Case View** — Tabbed view (Overview, Timeline, Evidence, IOCs, Findings, Playbook Runs, Report)
- **Playbooks** — Forensic analysis playbook cards with launch capability
- **Settings** — MCP host selector, API key management, system health monitoring

## API

All API calls target `http://localhost:8800`. The UI includes demo/fallback data when the API is unavailable.
