## Running the app locally

### Running the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On startup the app creates `backend/booksy.db` (SQLite), bootstraps the admin account, and seeds hardware from `../seed.json`. Interactive API docs are at `http://127.0.0.1:8000/docs`.

Run the test suite with:

```bash
cd backend
source .venv/bin/activate
pytest
```

Tests run against an isolated in-memory SQLite database (via a `get_db` dependency override) and never touch `backend/booksy.db`. The semantic-search tests mock the Anthropic client, so the suite never makes a real API call or needs a key.

#### Enabling semantic search

The "Ask AI…" hardware search needs a real Anthropic API key:

1. Get one from [console.anthropic.com](https://console.anthropic.com) (Settings → API Keys). API usage is billed separately from any Claude.ai plan.
2. Copy `backend/.env.example` to `backend/.env` (already done for local dev — just edit `backend/.env`) and fill in `ANTHROPIC_API_KEY=sk-ant-...`. `backend/.env` is gitignored and loaded automatically on startup via `python-dotenv` — never commit it.
3. Optionally override the model via `ANTHROPIC_SEARCH_MODEL` in the same file (defaults to `claude-sonnet-5`).

Without a key set, `/hardware/semantic-search` responds `503` with a friendly message — the rest of the app is unaffected.

### Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Starts the Vite dev server at `http://localhost:5173`. It expects the backend running at `http://127.0.0.1:8000` (override via `VITE_API_BASE_URL`). Log in with the bootstrapped admin credentials (or any user created via the admin API).
