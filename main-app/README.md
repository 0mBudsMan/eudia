# Legal Intelligence Suite

This Next.js 16 project combines the **Legal Case Analyzer** from `main-app` and the **ContractDraft AI workspace** from `my-app` into a single codebase. Use it to research case law and generate/iterate on NDAs, service agreements, or offer letters without switching projects.

## Features
- `/` &mdash; submit briefs, simulate verdict analysis, and review detailed case summaries in a modal viewer.
- `/contracts` &mdash; jump into ContractDraft with a dashboard, template-driven form builder, live preview, refinement chat, and export actions (TXT/PDF/Print/Copy).
- API routes backed by Google Gemini (`/api/generate-contract`, `/api/refine-contract`) and a HuggingFace-powered next-word helper for the custom editor.
- Shared UI kit (Radix + Tailwind), component library, and utilities so both experiences keep the same design language.

## Getting Started
1. Install dependencies (peer deps from `vaul` currently require the legacy resolver):
   ```bash
   npm install --legacy-peer-deps
   ```
2. Add the required environment variable in `.env.local`:
   ```bash
   GEMINI_API_KEY=your_google_generative_ai_key
   ```
3. Run the dev server:
   ```bash
   npm run dev
   ```
4. Open `http://localhost:3000` for the Case Analyzer or `http://localhost:3000/contracts` for ContractDraft.

## Available Scripts
- `npm run dev` – start Next.js in development mode.
- `npm run build` – create a production build.
- `npm run start` – serve the production build.
- `npm run lint` – runs ESLint (install `eslint` locally if it is not already available).

## Notes
- Contract generation/refinement requires a valid `GEMINI_API_KEY`. Without it, the API routes respond with `500`.
- The custom draft editor lazily loads `@gradio/client` from HuggingFace; the first request may take a moment while the client initializes.
- The dashboard persists generated NDAs in `localStorage`, so data is per-browser and non-persistent across devices.
