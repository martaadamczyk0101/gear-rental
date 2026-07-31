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

## Not built yet

- Admin command center endpoints/UI (hardware CRUD, repair toggle, notes, user creation)
- Dashboard (filter/sort) and rental (rent/return, my rentals) endpoints/UI
- Frontend (Vue 3 + Vite)
- Real session/token-based authentication
- LLM-powered natural-language hardware search (explicitly deferred — see `PLAN.md`)
