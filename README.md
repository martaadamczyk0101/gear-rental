# Internal Hardware Rental Tool

An internal tool for tracking company hardware (laptops, phones, peripherals, etc.), letting employees rent and return gear, and giving admins a command center to manage the hardware catalog and user accounts.

This README is updated as each feature is delivered — see `PLAN.md` for the full delivery plan and phase breakdown.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite, `anthropic` SDK (Claude Sonnet 5) for semantic search
- **Frontend**: Vue 3 + Vite, Pinia (state), Vue Router

## Features implemented so far

- **Admin bootstrap**: on first run, an admin account is created automatically from `BOOKSY_ADMIN_EMAIL` / `BOOKSY_ADMIN_PASSWORD` env vars (defaults: `admin@booksy.com` / `admin123` for local dev — override these for anything beyond local dev).
- **Hardware seeding**: `seed.json` is loaded into the database on first run. The seeder validates and normalizes each row rather than trusting the file blindly:
  - rows with a duplicate source `id`, an empty `name`/`brand`, or an unrecognized `status` are skipped (and logged as a warning)
  - a `purchaseDate` that doesn't parse as `YYYY-MM-DD` is stored as `null` (row is still seeded) and logged as a warning
  - `status` values are normalized case-insensitively (`"In Use"` → `in use`, `"Repair"` → `in repair`, etc.)
  - two informational fields present on some seed rows (`assignedTo`, `history`) aren't part of the current schema and are ignored — a hardware item seeded as `in use` is not automatically linked to a rental record
- **Login (MVP)**: `POST /auth/login` verifies email/password and returns the user's id/email/is_admin.
- **Admin command center API**:
  - `GET /hardware` — list hardware, with filtering and sorting (any authenticated user; see Dashboard below)
  - `POST /hardware` — create a hardware item (admin only, always starts `available`)
  - `DELETE /hardware/{id}` — delete a hardware item (admin only; blocked with `409` while the item is `in use`)
  - `PATCH /hardware/{id}/repair-toggle` — toggle between `available` and `in repair` (admin only; blocked with `409` while `in use`, so an item can't be pulled for repair out from under the person using it)
  - `PATCH /hardware/{id}/notes` — update an item's notes (admin only)
  - `POST /users` — create a user account with email/password/is_admin (admin only; the only way to gain access to the system; `409` on duplicate email)
- **Dashboard: filtering & sorting** — `GET /hardware` accepts `status` (`available`/`in use`/`in repair`), `brand` (substring match) and `search` (substring match on name) filters, plus `sort_by` (`name`/`brand`/`purchase_date`/`status`) and `sort_dir` (`asc`/`desc`).
- **Rental business logic**:
  - `POST /hardware/{id}/rent` — admin callers rent immediately (atomic conditional DB update, `UPDATE ... WHERE status='available'`, so two simultaneous requests for the same item can't both succeed — the loser gets `409`); everyone else's call now goes through the request/approval workflow below instead of renting directly. Always `409`s for items that are `in use` or `in repair`.
  - `POST /hardware/{id}/return` — return an item (owner or admin only; `403` otherwise). `409` if the item isn't currently rented.
  - `GET /rentals/mine` — the current user's open (not yet returned) rentals, with hardware details nested — powers the "My Rentals" tab.
  - Covered by an automated `pytest` suite (`backend/tests/`) exercising the state machine: admin instant-rent, conflicts on already-rented/in-repair items, return success/authorization, and filter/sort behavior.
- **Rental request/approval workflow** (`PLAN.md` Part 3, backend only so far):
  - When a non-admin calls `POST /hardware/{id}/rent`, instead of renting immediately it creates a `RentalRequest` (`pending`) and leaves the hardware `available` — multiple users can hold pending requests for the same item at once. The response shape changed to `{"outcome": "rented" | "requested", "hardware": {...}}` so callers can tell the two paths apart. A user can't submit a second pending request for the same item (`409`).
  - `GET /rental-requests` (admin only, `?status=pending|approved|rejected`, defaults to `pending`) — list requests with nested hardware + requester info.
  - `GET /rental-requests/pending-count` (admin only) — `{"pending": N}`, meant to drive a sidebar badge (not wired into the UI yet).
  - `POST /rental-requests/{id}/approve` (admin only) — re-runs the same atomic conditional update used by the direct-rent path (so it can't double-book against a race), creates the `Rental`, and **auto-rejects every other still-pending request for the same hardware** in the same transaction — this is what makes competing requests for one item "unavailable to accept" once one is approved. `409` if the item became unavailable in the meantime, or if the request was already decided.
  - `POST /rental-requests/{id}/reject` (admin only) — manual rejection; `409` if already decided.
  - `GET /rental-requests/mine` (any authenticated user) — the caller's own pending requests.
  - Covered by two `pytest` files: `test_rentals.py` (admin-vs-user branching, duplicate-request guard, two users holding simultaneous pending requests) and `test_rental_requests.py` (list/count/approve/reject, the sibling-auto-rejection scenario, the race-guard on approve, already-decided guard, 404/403 authorization). Verified live end-to-end: two users request the same item, hardware stays `available`, approving one flips it to `in use` and the sibling request both disappears from the pending queue and 409s if approval is attempted anyway.
  - **Not built yet**: the frontend side of this (toast on submit, disabled "Requested" state on the Dashboard, the admin panel's Rental Requests section, the sidebar badge) — see `PLAN.md` Part 3.
- **Frontend foundation**:
  - Login page (`/login`) that calls `POST /auth/login` and, on success, stores the returned user (id/email/is_admin) in a Pinia store, persisted to `localStorage` so a page refresh doesn't log you out.
  - An API client (`src/api/client.js`) that automatically attaches the `X-User-Id` header to every request based on the logged-in user.
  - Router guards: unauthenticated users are redirected to `/login` (preserving where they were headed, so login lands them back where they intended to go); non-admins are redirected away from `/admin`.
- **Dashboard & My Rentals UI**:
  - Dashboard table (device name, brand, purchase date, status) backed by the filter/sort API: a search box (debounced), a status dropdown, and clickable sortable column headers (with an asc/desc indicator).
  - A `Rent` button on each available item; unavailable items show a disabled button instead. Renting refreshes the table so status updates immediately.
  - `My Rentals` page lists the current user's open rentals with a `Return` button; returning refreshes the list.
  - A shared `StatusBadge` component renders the three statuses consistently (`available` / `in use` / `in repair`) across both views.
  - Verified end-to-end in a real browser (Playwright): search, status filter, and both sort directions all return the correct rows; renting an item moves it into "My Rentals" and makes it disappear again after returning; console had zero errors.
- **Visual design system**: black `#000000` / white `#ffffff` / teal `#05cfa6` (used for the primary highlight/action color, e.g. the Return button and input focus rings), headings in Poppins (extra bold), body text in Inter — a free, metrics-compatible stand-in for Proxima Nova (which requires a commercial license), loaded via Google Fonts in `index.html`. Design tokens live in `src/style.css`. Layout is a left sidebar (nav + current user + logout) with content on the right, based on internal design reference screenshots.
- **Admin Command Center UI** (`/admin`):
  - Hardware Management table with an "Add New Device" toggle form (name/brand/purchase date/notes), a wrench icon to toggle repair status, and a trash icon to delete — both icons are disabled (matching the backend's `409` guards) whenever an item is `in use`, so the UI can't even attempt an impossible transition.
  - Notes are edited inline: clicking the notes cell turns it into a textarea with Save/Cancel.
  - A "Create User" form (email/password/admin checkbox) calls the admin-only user-creation endpoint and shows a success or error message (e.g. duplicate email).
  - Verified end-to-end in a real browser (Playwright): added and deleted a test device, edited its notes, toggled repair status both directions, confirmed the repair/delete buttons are disabled for an `in use` item, created a user, and confirmed a duplicate email is rejected with a visible error.
- **Polish pass**:
  - Fixed a real contrast bug: the page previously followed the OS `prefers-color-scheme`, but only `--text`/`--bg`/`--surface`/`--border` had dark-mode overrides while the gray/status tokens (e.g. the "In Use" badge background) didn't, so a dark-mode visitor would see illegible light-gray-on-white-turned-dark text. Since the whole visual system is an intentionally light black/white/teal brand (not a dual light/dark design), the fix is to pin `color-scheme: light` rather than half-support a broken dark theme. Verified with the browser's color scheme emulated to `dark`: the app still renders correctly in light mode.
  - De-duplicated CSS across all four views into shared global classes in `src/style.css` (`.btn`/`.btn-primary`/`.btn-accent`, `.data-table`, `.error`/`.success`) instead of every view repeating near-identical button/table rules.
  - Replaced the default Vite/Vue scaffold favicon with a favicon matching the login page's icon.
  - Re-verified the full Playwright suite (dashboard filter/sort/rent, my rentals/return, admin CRUD/repair-toggle/notes/user-creation) against the refactored styles — all still pass with no visual regressions.
- **LLM-powered semantic search** (Part 2 of `PLAN.md`):
  - `GET /hardware/semantic-search?q=<query>` (any authenticated user) sends the natural-language query plus the *full* current inventory (id/name/brand/purchase_date/notes/status — every field the model might need to reason about) to Claude (`claude-sonnet-5` via the `anthropic` SDK, `backend/app/llm.py`), using **Structured Outputs** (`output_format`) so the response is a guaranteed-parseable `{"matching_ids": [...]}` — no free-text parsing. Searches the whole inventory regardless of status; it's a discovery tool, not a rent-only shortcut.
  - Fails gracefully: `422` on an empty/missing query, `503` ("Semantic search is temporarily unavailable — try the filters instead") if `ANTHROPIC_API_KEY` isn't set or the Anthropic API errors — the rest of the dashboard keeps working either way.
  - Dashboard UI: an "Ask AI…" box above the regular filters, submitted on Enter/click (not per-keystroke, since each submission is a billed API call). Shows AI-matched results in the same table/styling, with a "back to browsing" link to return to the normal filtered/sorted view.
  - Covered by `pytest` with a mocked Claude client (empty query, missing key, API error, successful match, and a dedicated regression test asserting `purchase_date`/`brand`/`notes` are actually present in the payload sent to the model — no real API calls in the test suite).
  - Verified live against the real Anthropic API with a real key: "devices purchased before 2023" correctly returns exactly the 6 items dated 2021–2022 (excluding the 2023 item, a future-dated 2027 item, and one item with no purchase date on file); "something to test a mobile app on" returns the phones/tablets; a bluetooth-headphones query returns the headphones.
  - **Fixed bug**: an early version built the inventory payload with only `id`/`name`/`brand`/`notes`/`status` — `purchase_date` was silently omitted, so any date-based query (e.g. "purchased before 2023") had no way to match, regardless of prompt wording. Fixed by including `purchase_date` in the payload and updating the system prompt to explicitly call out date-based reasoning.

### Known limitation: MVP auth

There is **no real session/token system yet**. After logging in, the frontend is expected to remember the returned user and send an `X-User-Id` header on subsequent requests; the backend trusts that header as-is to identify the caller (see `get_current_user` in `backend/app/auth.py`). This is intentionally insecure (the header can be forged) — it exists to get the full workflow (admin CRUD, rent/return, filtering) working end-to-end quickly. It will be replaced with real session/token-based auth in a later phase.

## Project Structure

```
booksy/
  backend/
    app/
      main.py        # FastAPI app, CORS, startup seeding
      config.py       # env-driven settings
      database.py      # SQLAlchemy engine/session
      models.py         # User, Hardware, Rental, RentalRequest
      schemas.py         # Pydantic request/response models
      auth.py             # password hashing + MVP auth dependency
      seed.py               # seed.json validation/normalization + admin bootstrap
      llm.py                  # Anthropic client wrapper for semantic search (structured output)
      routers/
        auth.py               # /auth/login, /auth/logout, /auth/me
        hardware.py            # hardware CRUD, repair-toggle, notes (admin) + filtered/sorted list (any user)
        rentals.py              # rent/return (atomic status guard, admin-vs-user branching) + my-rentals
        rental_requests.py        # request/approve/reject workflow (list, pending-count, mine)
        search.py                # /hardware/semantic-search (LLM natural-language search)
        users.py                # admin-only user creation
    tests/                        # pytest suite for the rental state machine, approval workflow, filters/sort, and semantic search
    requirements.txt
    .env.example                    # template for local secrets (copy to .env, gitignored)
  frontend/
    src/
      main.js, App.vue
      api/client.js            # fetch wrapper, attaches X-User-Id
      stores/auth.js            # Pinia auth store (login/logout, localStorage persistence)
      router/index.js            # routes + auth/admin guards
      components/StatusBadge.vue
      views/
        LoginView.vue, DashboardView.vue, MyRentalsView.vue, AdminView.vue
    package.json
  seed.json
  PLAN.md
  README.md
```

## Running the backend

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

### Enabling semantic search

The "Ask AI…" hardware search needs a real Anthropic API key:

1. Get one from [console.anthropic.com](https://console.anthropic.com) (Settings → API Keys). API usage is billed separately from any Claude.ai plan.
2. Copy `backend/.env.example` to `backend/.env` (already done for local dev — just edit `backend/.env`) and fill in `ANTHROPIC_API_KEY=sk-ant-...`. `backend/.env` is gitignored and loaded automatically on startup via `python-dotenv` — never commit it.
3. Optionally override the model via `ANTHROPIC_SEARCH_MODEL` in the same file (defaults to `claude-sonnet-5`).

Without a key set, `/hardware/semantic-search` responds `503` with a friendly message — the rest of the app is unaffected.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Starts the Vite dev server at `http://localhost:5173`. It expects the backend running at `http://127.0.0.1:8000` (override via `VITE_API_BASE_URL`). Log in with the bootstrapped admin credentials (or any user created via the admin API).

## Not built yet

The full MVP (backend + frontend, `PLAN.md` Phases 1–7) and the semantic search feature (`PLAN.md` Part 2, Phase 8) are built and live-verified. Part 3 (`PLAN.md`) is in progress:

- Real session/token-based authentication (currently the MVP's trusted `X-User-Id` header — see "Known limitation" above)
- Rental approval workflow: **backend done** (see above); frontend still needed — the submit toast, the Dashboard's disabled "Requested" button state, the admin panel's Rental Requests section, and the sidebar pending-count badge
- Admin UI polish from `PLAN.md` Part 3: Add Device/Create User modals, the hardware Edit action, future-purchase-date validation, fixed-width status pills, and filter/sort/search on the admin hardware table
