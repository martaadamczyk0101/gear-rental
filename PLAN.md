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

---

# Part 2 — LLM Semantic Search Integration

## Context

The MVP (Phases 1–7 above) is complete. This part covers the natural-language hardware search the user wants next: a user types something like *"I need something to test a mobile app on"* and gets back relevant items (iPhones, Android devices) even though none of those words appear in the hardware's name/brand/notes fields. This requires an LLM to bridge the gap between intent and inventory — plain substring search (already built in Phase 3/5) can't do this.

Decisions confirmed with the user:
- **Model**: `claude-sonnet-5`, via the official `anthropic` Python SDK. This deliberately departs from Anthropic's own default guidance (which is to use `claude-opus-5` for new integrations unless told otherwise) — this feature fires on every search submission from an interactive UI, so per-query latency and cost matter more here than they would for a one-off task, and Sonnet 5 comfortably handles a straightforward "match this need to these ~10 items" classification job. The user chose Sonnet 5 over the faster/cheaper Haiku 4.5 option for extra reasoning headroom on ambiguous queries.
- **Approach**: a single non-streaming Claude API call per search, using **Structured Outputs** (`output_config.format`, via `client.messages.parse()`) to force a guaranteed-parseable `{"matching_ids": [...]}` response — not a vector database / embeddings pipeline. The inventory is small (dozens of items), so sending the full list as context on every query is simpler and cheap enough; embeddings would be premature infrastructure at this scale and can be revisited if the catalog grows much larger.
- **Scope**: semantic search runs against the *entire* inventory regardless of status (available/in use/in repair) — it's a discovery tool ("what do we own that fits this need"), not a shortcut that only surfaces rentable items. The existing status filter and the rent button already handle availability once the user sees the results.

## Architecture

- **New backend module** `backend/app/llm.py`: a thin wrapper around `anthropic.Anthropic()`. Builds the prompt (system instructions + the query + the current inventory as JSON), calls `client.messages.parse()` with a Pydantic output model `HardwareMatch(BaseModel): matching_ids: list[int]`, and returns the parsed list of ids. Raises a specific `SemanticSearchUnavailable` exception if `ANTHROPIC_API_KEY` isn't configured, so the router can turn that into a clean error response instead of a 500 crash.
- **New endpoint** `GET /hardware/semantic-search?q=<query>` (any authenticated user, new `routers/search.py`):
  1. Reject an empty/missing `q` with `400`.
  2. Load the full hardware inventory (id, name, brand, notes, status) — no status filter.
  3. Call `app/llm.py` to get back matching ids.
  4. Look up those rows and return them via the existing `HardwareOut` schema, in the order Claude returned the ids (an implicit relevance ranking).
  5. On `SemanticSearchUnavailable` or any Anthropic API error/timeout, return `503` with a message like "Semantic search is temporarily unavailable — try the filters instead" — the rest of the dashboard must keep working even if this feature is down.
- **Config additions** (`app/config.py`): `ANTHROPIC_API_KEY` (no default — required for the feature to work at all) and `ANTHROPIC_SEARCH_MODEL` (defaults to `claude-sonnet-5`, overridable without a code change).
- **Frontend**: an "Ask AI…" input added to the Dashboard (matching the sparkle-icon mockup), visually separate from the existing status/search filter row. Submits on Enter or a button click — **not** on every keystroke like the existing debounced substring search, since each submission is a billed API call. While showing AI results: reuse the existing `.data-table`/`StatusBadge` styling, show a loading state (the call can take a couple of seconds), and offer a "Clear" action to return to the normal filter/sort view. The existing deterministic filter/sort controls are untouched and remain the fast default path; the AI box is an alternate, opt-in way to populate the same table.

## Prompt Design

- **System prompt**: instructs Claude to act as a hardware-matching assistant — given a natural-language need and a JSON inventory list (id/name/brand/notes/status), return the ids of items that would satisfy that need, using both explicit device-type matches and general domain knowledge (e.g., "mobile app testing" implies phones/tablets); return an empty list if nothing is relevant; never invent an id that isn't in the provided list.
- **User content**: the raw query plus the serialized inventory JSON.
- **Structured output schema**: `{"type": "object", "properties": {"matching_ids": {"type": "array", "items": {"type": "integer"}}}, "required": ["matching_ids"], "additionalProperties": false}`, requested via `output_config.format` so the response is guaranteed valid JSON — no free-text parsing.

## Testing Strategy

- `pytest`: monkeypatch `app.llm.find_matching_ids` so the test suite never calls the real Anthropic API (no cost, no network flakiness in CI). Covers: empty query → `400`; missing API key → `503`; a mocked successful match → correct hardware rows returned in the right order.
- Live verification (manual + Playwright) requires a real `ANTHROPIC_API_KEY` and will run once implemented, using a few realistic queries (e.g. "something to test a mobile app on" → phones/tablets, "I need a laptop for a client presentation" → laptops, "I need to check whether the issue with the app also occurs when using bluetooth headphones → bluetooth headphones) to sanity-check real-world relevance.

## Known Limitations / Explicitly Deferred

- No caching of repeated/identical queries — fine at this traffic scale; revisit if usage grows.
- No rate limiting on the endpoint — internal tool with a small trusted user base; add if it becomes a cost concern.
- No embeddings/vector database — acceptable while the catalog stays in the dozens-to-low-hundreds of items; would need a different architecture (embedding index, similarity search) if the inventory grows much larger.

## Delivery Phase

8. **Semantic search** — `backend/app/llm.py` (Anthropic client wrapper + structured-output prompt), `GET /hardware/semantic-search` endpoint, and an "Ask AI…" search box on the Dashboard.
   - *Verify*: `pytest` suite with a mocked Claude client covering the error paths (missing key, empty query) and a mocked success path; live check with 2–3 realistic natural-language queries against the real API once an `ANTHROPIC_API_KEY` is available.

---

# Part 3 — Rental Approval Workflow & Admin UI Polish

## Context

Final adjustment pass before wrapping up. The biggest change is a business-logic shift: renting is no longer instant for regular users — it becomes a request that an admin must approve, so admins keep control over who gets what. Everything else in this part is admin-panel UX polish (modals instead of inline forms, an edit action, matching the Dashboard's filter/sort/search on the admin table, consistent pill widths, and a purchase-date guard) driven by the reference screenshots the user attached.

Two implementation gaps were filled in with a default decision (called out explicitly below) since the request didn't spell them out: how the requester sees their own pending/rejected requests, and how the admin is notified of new ones.

## Rental Approval Workflow

**Behavior change**: `POST /hardware/{id}/rent` no longer immediately rents the item for a regular user. Instead:

- **Admin caller**: unchanged — immediate atomic rent, exactly like today (this is the "except for admins" carve-out).
- **Regular user caller**: instead of flipping `Hardware.status`, creates a `RentalRequest(status="pending")`. The hardware **stays `available`** and other users can still submit their own requests for the same item — the whole point of the "two or more requests for the same gear" scenario is that multiple pending requests can coexist until an admin decides.
- Guard: a user can't submit a second pending request for an item they've already requested (`409`) — otherwise the same person spamming "Rent" would flood the queue.
- Guard: requesting an item that isn't `available` (`in use` / `in repair`) still `409`s immediately, same as today — no point queuing a request for gear that clearly isn't obtainable right now.

**New data model**: `RentalRequest`: `id`, `hardware_id` (FK), `user_id` (FK, the requester), `status` (`pending` / `approved` / `rejected`), `requested_at`, `decided_at` (nullable), `decided_by_user_id` (FK, nullable — which admin decided it). No migration tooling needed — `Base.metadata.create_all` picks up the new table automatically on next startup, same as every table so far.

**New admin-only endpoints** (`backend/app/routers/rental_requests.py`):
- `GET /rental-requests?status=pending` — list requests (hardware + requester info nested) for the admin panel's new section.
- `GET /rental-requests/pending-count` — a cheap `{"pending": N}` used only to drive the sidebar badge, so the whole app doesn't need to poll the full list just to show a number.
- `POST /rental-requests/{id}/approve` — atomically re-checks `hardware.status == 'available'` (the same conditional-`UPDATE` pattern used by the existing rent endpoint) before creating the `Rental` row and flipping the hardware to `in use`; `409` if it lost the race. On success, **every other pending `RentalRequest` for the same `hardware_id` is auto-rejected in the same transaction** — this is the concrete mechanism behind "the others must become unavailable to accept": they simply vanish from the admin's pending queue once one request wins.
- `POST /rental-requests/{id}/reject` — manual rejection (the request didn't specify this, but "approve" implies its opposite is needed for the workflow to be usable at all — otherwise an admin has no way to dismiss a request they don't want to grant).
- `409` on approve/reject if the request isn't still `pending` (e.g. two admins acting on it at once, or it was already auto-rejected by a sibling approval).

**Filled gap #1 — requester visibility**: `GET /rental-requests/mine` (any authenticated user) lists the caller's own pending requests. Two places use it:
- Dashboard: cross-referenced against the hardware list so an item the user already requested shows a disabled "Requested" button instead of "Rent" (prevents the confusing "why did clicking Rent again do nothing new" case, and is what makes the duplicate-request guard above actually make sense in the UI).
- My Rentals: a small "Pending Requests" section above the existing active-rentals table, so a user has somewhere to check status instead of relying solely on the one-time toast.

**Filled gap #2 — admin notification**: a small badge with the pending count next to the "Admin Panel" sidebar link (admins only), polling `GET /rental-requests/pending-count` every ~20–30s while an admin session is open. No websockets/real-time push — plain polling is enough at this scale, consistent with how the rest of this MVP has favored the simplest workable mechanism.

**Admin panel — new "Rental Requests" section**: a third stacked section in `AdminView.vue` (after Hardware Management, before or after Create User) — table of device name / brand / requested by / requested at, with Approve / Reject buttons per row. Refetches after every decision, which is also how the "sibling requests disappear" behavior becomes visible.

## Request-Submitted Feedback

Per the reference screenshot: a toast/snackbar (white rounded card, shadow, checkmark icon, auto-dismiss after a few seconds) appears after clicking Rent. Implemented as a small global toast composable/component mounted once in `App.vue`, message text branches on the rent endpoint's outcome:
- Admin (instant rent): "Rented \<item name\>."
- Regular user (queued): "Rental request submitted for \<item name\>."

This means `POST /hardware/{id}/rent`'s response shape needs to say which of the two happened — it now returns `{"outcome": "rented" | "requested", "hardware": {...}}` instead of the bare hardware object, so the frontend knows which toast text and which table-refresh behavior to apply.

## Admin UI Polish

- **Add Device modal**: the existing inline collapsible "Add New Device" form in `AdminView.vue` becomes a real modal (centered card, dark backdrop, title + subtitle, Cancel / Add Device buttons) matching the attached screenshot's layout — but with **our** fields, not the mockup's: Name, Brand, Purchase Date, Notes. (No Serial Number or Category — those aren't part of our schema and weren't asked for.)
- **Create User modal**: the inline "Create User" form becomes a modal using the same visual component/style as the Add Device modal (Email, Password, Admin checkbox, Cancel / Create User buttons).
- **Edit action**: a new pencil icon in the Actions column, next to the existing wrench (repair-toggle) and trash (delete) icons. Opens the same modal component used for "Add Device," in an edit mode — pre-filled with the item's current name/brand/purchase_date/notes, submit button reads "Save Changes." This needs a real edit endpoint: `PATCH /hardware/{id}` (admin only, partial update of name/brand/purchase_date/notes) — replacing the current notes-only `PATCH /hardware/{id}/notes`, so the table's existing inline notes quick-edit and the new modal both call the same endpoint.
- **Purchase date can't be in the future**: enforced in two places — the date `<input>`'s `max` attribute (both Add and Edit modals) is clamped to today for a good UX, and the same rule is enforced server-side in the `HardwareCreate`/new `HardwareUpdate` schemas (client-side `max` is just UX, not the actual guard — the same principle already applied everywhere else in this app, e.g. the atomic rent guard).
- **Status pills, consistent width**: `StatusBadge.vue`'s `.badge` class gets a fixed width (sized to fit "In Repair," the longest label) instead of the current auto/content-based width, with text centered — so "Available," "In Use," and "In Repair" all render as same-size pills, matching the reference screenshot.
- **Hardware Management gets the Dashboard's filter/sort/search**: the admin table currently just lists everything unfiltered. It gets the same status filter, name search box, and sortable column headers already built for the Dashboard, wired to the same `GET /hardware` query params — no backend changes needed here, just porting the existing frontend filter/sort state logic into `AdminView.vue` (worth considering a small shared composable between the two views instead of copy-pasting the same state/handlers twice, decided at implementation time).

## Testing Strategy

- `pytest`: the approval workflow is exactly the kind of "prevent impossible states" logic this project has prioritized testing throughout — cover: a regular user's rent request creates a pending `RentalRequest` without changing hardware status; an admin's rent request rents immediately; a duplicate pending request from the same user `409`s; approving one of several pending requests for the same hardware auto-rejects the others; approving after the hardware became unavailable (race) `409`s; rejecting/approving an already-decided request `409`s; the purchase-date-in-the-future guard rejects on both create and edit.
- Manual/Playwright: submit a request as a regular user and see the toast + disabled "Requested" button; approve it as admin and confirm the item flips to `in use` and appears in the requester's My Rentals; create two competing requests for one item and confirm approving one makes the other disappear from the pending queue; exercise the new Add/Edit/Create-User modals and confirm the date picker won't accept a future date; confirm the admin table's new filter/search/sort behaves identically to the Dashboard's.

## Known Limitations / Explicitly Deferred

- No real-time push for the admin badge or requests list — polling only, consistent with the rest of this MVP's "simplest workable mechanism" approach.
- No way for a user to cancel their own pending request — they can only wait for an admin decision (or ask the admin to reject it out of band).
- Rejected requests aren't actively surfaced to the user beyond appearing (then disappearing) from "Pending Requests" in My Rentals — no separate rejection notification.

## Delivery Phase

9. **Rental approval workflow** — `RentalRequest` model, `routers/rental_requests.py` (list/pending-count/approve/reject/mine), the `POST /hardware/{id}/rent` outcome-branching change, the toast component, the Dashboard's disabled "Requested" state, My Rentals' "Pending Requests" section, and the admin sidebar badge.
   - *Verify*: `pytest` covering the state machine (pending vs. immediate admin rent, duplicate-request guard, sibling auto-rejection on approval, race guard, already-decided guard); live walkthrough of the full request → approve/reject → rented-or-still-available cycle.
10. **Admin UI polish** — Add Device and Create User modals, the new Edit action and `PATCH /hardware/{id}` endpoint, the future-purchase-date guard (client + server), fixed-width status pills, and filter/sort/search on the admin Hardware Management table.
    - *Verify*: manual click-through of every modal and the edit flow; confirm a future purchase date is rejected in both modals; visually confirm all three status pills render the same width; confirm the admin table's filter/search/sort matches the Dashboard's behavior.
