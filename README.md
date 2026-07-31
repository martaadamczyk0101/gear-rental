# Internal Hardware Rental Tool

An internal tool for tracking company hardware (laptops, phones, peripherals, etc.), letting employees rent and return gear, and giving admins a command center to manage the hardware catalog and user accounts.

This README is updated as each feature is delivered — see `PLAN.md` for the full delivery plan and phase breakdown.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vue 3 + Vite (not yet built — see PLAN.md)

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
  - `POST /hardware/{id}/rent` — rent an item (any authenticated user). Uses an atomic conditional DB update (`UPDATE ... WHERE status='available'`) so two simultaneous requests for the same item can't both succeed — the loser gets `409`. Also `409`s for items that are `in use` or `in repair`.
  - `POST /hardware/{id}/return` — return an item (owner or admin only; `403` otherwise). `409` if the item isn't currently rented.
  - `GET /rentals/mine` — the current user's open (not yet returned) rentals, with hardware details nested — powers the "My Rentals" tab.
  - Covered by an automated `pytest` suite (`backend/tests/`) exercising the state machine: rent success, conflicts on already-rented/in-repair items, return success/authorization, and filter/sort behavior.

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
      models.py         # User, Hardware, Rental
      schemas.py         # Pydantic request/response models
      auth.py             # password hashing + MVP auth dependency
      seed.py               # seed.json validation/normalization + admin bootstrap
      routers/
        auth.py               # /auth/login, /auth/logout, /auth/me
        hardware.py            # hardware CRUD, repair-toggle, notes (admin) + filtered/sorted list (any user)
        rentals.py              # rent/return (atomic status guard) + my-rentals
        users.py                # admin-only user creation
    tests/                        # pytest suite for the rental state machine and filters/sort
    requirements.txt
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

Tests run against an isolated in-memory SQLite database (via a `get_db` dependency override) and never touch `backend/booksy.db`.

## Not built yet

- Admin command center UI and Dashboard/My Rentals UI (the APIs are done; no frontend yet)
- Frontend (Vue 3 + Vite)
- Real session/token-based authentication
- LLM-powered natural-language hardware search (explicitly deferred — see `PLAN.md`)
