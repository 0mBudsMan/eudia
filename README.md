## Development Shortcuts

Use `scripts/run_everything.sh` to boot the FastAPI research backend and the Next.js frontend from a single command.

```bash
./scripts/run_everything.sh \
  --facts-file path/to/case.txt   # optional: refresh legal_analysis_results.json first
```

Key flags:

- `--facts "<text>"` or `--facts-file <path>`: run `python main.py ...` before starting servers so the workflow outputs are up to date.
- `--port <number>`: change the backend port (defaults to `8000`); the script also sets `NEXT_PUBLIC_RESEARCH_API_URL`.
- `--skip-pipeline`: skip the LangGraph workflow entirely if you want to reuse the last analysis run.

Prerequisites: install Python deps (`pip install -r requirements.txt`), install frontend deps (`cd main-app && npm install --legacy-peer-deps`), and set your Gemini key via `GEMINI_API_KEY`/`GOOGLE_API_KEY` before running the optional workflow step.
