# WURI Ranking Readiness DSS — Frontend Snapshot

This folder contains a **quarantined, non-operational snapshot**. `index.html` directly renders a standalone static HTML/CSS security-hold notice. The tracked React component is not mounted: `src/main.jsx` is absent and the HTML contains no module script. This is not a functioning ranking-readiness system.

## Technology stack

| Area | Technology | Evidence in this repository |
|---|---|---|
| Programming language | JavaScript (ES modules) | `package.json` uses `"type": "module"`; source/config files use `.js` and `.jsx` |
| UI library | React 18 declared, but not active | Dependencies are declared; no tracked React entrypoint mounts the component |
| Component syntax | JSX source fragment | `src/App.jsx` exists but is not loaded; `src/main.jsx` is absent |
| Build/dev tooling | Vite declared | `vite.config.js` and package scripts exist; runtime/build not verified |
| Styling | CSS + Tailwind CSS 4 | `src/index.css`, Tailwind import and Vite plugin |
| Routing | React Router 7 | `BrowserRouter`, `Routes`, and `Route` |
| Icons | Lucide React | `ShieldCheck` in `src/App.jsx` |
| Static code analysis config | ESLint | `eslint.config.js` |

There is currently **no backend implementation or backend programming language** in this repository snapshot. Python/FastAPI, Node.js API services, Supabase integration, authentication, document processing, and ranking algorithms are not implemented here.

## Important status

Do not upload institutional documents or enter credentials. The security-hold screen is intentional until independent security review, credential containment, and explicit implementation/runtime authorization are complete.

No dependencies have been installed and no build, lint, test, or runtime command has been executed for this snapshot. The HTML page is standalone; the React component is currently disconnected from the page.
