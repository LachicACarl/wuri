# WURI Ranking Readiness DSS — Frontend Snapshot

This folder contains a **quarantined, non-operational frontend snapshot**. The application currently renders only a security-hold notice. It is not a functioning ranking-readiness system.

## Technology stack

| Area | Technology | Evidence in this repository |
|---|---|---|
| Programming language | JavaScript (ES modules) | `package.json` uses `"type": "module"`; source/config files use `.js` and `.jsx` |
| UI library | React 18 | `react` and `react-dom` dependencies |
| Component syntax | JSX | `src/App.jsx`, `src/main.jsx` |
| Frontend build/dev server | Vite | `vite.config.js` and Vite scripts |
| Styling | CSS + Tailwind CSS 4 | `src/index.css`, Tailwind import and Vite plugin |
| Routing | React Router 7 | `BrowserRouter`, `Routes`, and `Route` |
| Icons | Lucide React | `ShieldCheck` in `src/App.jsx` |
| Static code analysis config | ESLint | `eslint.config.js` |

There is currently **no backend implementation or backend programming language** in this repository snapshot. Python/FastAPI, Node.js API services, Supabase integration, authentication, document processing, and ranking algorithms are not implemented here.

## Important status

Do not upload institutional documents or enter credentials. The security-hold screen is intentional until independent security review, credential containment, and explicit implementation/runtime authorization are complete.

No dependencies have been installed and no build, lint, test, or runtime command has been executed for this snapshot.
