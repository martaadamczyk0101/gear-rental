# Internal Hardware Rental Solution — Delivery Plan

## Context

This is a greenfield internal tool (the project directory currently only contains `seed.json`). The company needs to track physical hardware (laptops, phones, peripherals) that employees borrow, with an admin-controlled access model (no self-signup), a browsing/renting experience for regular users, and a foundation that a future LLM-based natural-language search feature can be layered onto without rearchitecting. Decisions already confirmed with the user: FastAPI for the backend, admin sets user passwords directly at account-creation time, and the seed script must robustly validate/normalize `seed.json` rather than requiring the file itself to be clean (it intentionally contains bad rows: duplicate `id: 4`, an invalid `status: "Unknown"`, a malformed date `"22-05-2023"`, a `null` date, and an empty `brand`).

Auth was deliberately scoped down for the MVP: no server-side session store yet. `POST /auth/login` just verifies email/password and returns the user's id/email/is_admin. The frontend keeps that in memory/localStorage and re-identifies itself on every request via an `X-User-Id` header, which the backend trusts as-is (looking up the real user row to check `is_admin` for admin routes). **This is explicitly a placeholder with no real security** (the header can be forged) — acceptable for now since the goal is to get the full workflow (admin CRUD, rent/return, filtering) working end-to-end quickly; it is flagged in the README as a known limitation to replace with real session/token auth in a later phase.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy (2.0 style) for models/queries, Pydantic for request/response schemas, `bcrypt` for password hashing, SQLite as the database file.
- **Frontend**: Vue 3 + Vite, Pinia for state, Vue Router with navigation guards, native `fetch` (with `credentials: 'include'`) for API calls.
- **Auth (MVP)**: simple email/password login, no session/token persistence. User accounts are created by an administrator and stored in the database. A more robust authentication and authorization system will be implemented in a later phase.

## Data Model

- `User`: id, email, password_hash, is_admin, created_at
- `Hardware`: id, name, brand, purchase_date (nullable date), status (`available` / `in use` / `in repair`), notes (nullable text)
- `Rental`: id, hardware_id (FK), user_id (FK), rented_at, returned_at (nullable) — an open rental is `returned_at IS NULL`; this single table drives both "my rentals" and future full rental history.

No `Session` table for now — see the Auth note above (MVP uses a trusted `X-User-Id` header instead of server-side sessions).

Status transitions are enforced with an atomic conditional `UPDATE ... WHERE id=? AND status='available'` (checking affected row count) when renting, so two users cannot rent the same item in a race — this directly satisfies the "prevent impossible states" requirement. Admin can only toggle `in repair` on items that are currently `available` (not while `in use`), and hardware cannot be deleted while `in use` — both enforced server-side, not just hidden in the UI.

## Project Structure

```
booksy/
  backend/
    app/
      main.py, config.py, database.py, models.py, schemas.py, auth.py, seed.py
      routers/{auth.py, hardware.py, rentals.py, users.py}
    requirements.txt
  frontend/
    src/
      views/{LoginView.vue, DashboardView.vue, MyRentalsView.vue, AdminView.vue}
      components/{HardwareTable.vue, HardwareFormModal.vue, UserFormModal.vue}
      stores/{auth.js, hardware.js, rentals.js}
      router/index.js
      api/client.js
    package.json
  README.md
  PLAN.md
  seed.json
```

## Delivery Phases

1. **Backend foundation** — scaffold FastAPI app, SQLAlchemy models/DB init, config (admin bootstrap credentials via env vars, defaulted for local dev), the robust seed script (validates each `seed.json` row: normalizes status casing, parses/repairs or rejects bad dates, skips duplicate ids with a logged warning, requires non-empty brand/name), basic authentication (MVP): admin-created user accounts stored in the database (email + hashed password), a `POST /auth/login` that verifies credentials and returns the user's id/email/is_admin (no session persistence), and a `get_current_user` dependency that trusts an `X-User-Id` header for identifying the caller on subsequent requests (explicitly temporary, to be replaced by real sessions later). Also create initial `README.md`.
   - *Verify*: run `uvicorn`, hit `/docs`, the admin can log in and create user accounts, users can log in using their assigned credentials and then call a protected endpoint by passing `X-User-Id`, confirm seed rows loaded and bad rows were skipped/logged as expected.

2. **Admin command center API** — hardware CRUD (create/delete), repair-toggle endpoint (blocked unless status is `available`), notes update, user-creation endpoint. All guarded by an `require_admin` dependency.
   - *Verify*: exercise via `/docs` as admin and confirm a non-admin session gets 403.

3. **Dashboard & rental business-logic API** — `GET /hardware` with query-param filtering (status, brand, text search) and sorting (name/brand/purchase_date/status), `POST /hardware/{id}/rent` and `/return` with the atomic status-guard, `GET /rentals/mine`.
   - *Verify*: pytest cases — rent an available item succeeds; renting an already-rented or in-repair item returns 409; returning updates status back to available; a user can't return someone else's rental.

4. **Frontend foundation** — Vite/Vue 3 scaffold, Pinia auth store (holds the logged-in user, persisted to localStorage so a refresh doesn't log the user out, sends `X-User-Id` on every API call), router with guards (unauthenticated → login, non-admin blocked from `/admin`), `LoginView`.
   - *Verify*: log in through the actual UI and confirm subsequent API calls are correctly identified as that user.

5. **Dashboard + My Rentals UI** — hardware table (name/brand/purchase date/status) with filter and sort controls wired to the backend query params, rent/return buttons, "My Rentals" tab.
   - *Verify*: manually rent/return an item in the browser and watch status update live across tabs.

6. **Admin Command Center UI** — hardware management table (add/delete/repair-toggle/notes) and a user-creation form.
   - *Verify*: create a new user in the UI, log out, log in as that user.

7. **Polish & docs** — loading/error states, minor styling pass, finalize README against everything actually shipped.

**Not building yet (explicitly deferred)**: the LLM semantic search feature. The `Hardware` model's plain text fields (name, brand, notes) are sufficient for a future embedding/keyword-based `search` endpoint — no speculative scaffolding will be added for it now.

## README

Created in Phase 1 with: project overview, tech stack, feature list, setup/run instructions (backend venv + `pip install`, frontend `npm install`, how to run both dev servers, how to seed the DB, where the bootstrap admin credentials come from). Updated at the end of every subsequent phase to reflect newly shipped features. Reminders to commit will be given at the end of each phase (or sooner, if a chunk of work is independently meaningful).

## Verification Summary

- Backend: FastAPI's `/docs` Swagger UI for manual endpoint checks; `pytest` suite for the rental state-machine and auth/authorization guards (the correctness-critical logic called out in the requirements).
- Frontend: manual click-through in the browser (login → dashboard filter/sort → rent/return → My Rentals → Admin CRUD), since this is a UI-driven deliverable.
