## Tests

Backend only, there's no frontend test suite yet (frontend changes are verified manually)

43 tests across 5 files, all against an isolated in-memory SQLite database (`tests/conftest.py` overrides the `get_db` dependency with a `StaticPool` in-memory engine per test) — the suite never touches the real `backend/booksy.db`, and never makes a real Anthropic API call.

- **`test_hardware.py`** — the general `PATCH /hardware/{id}` endpoint: partial updates only touch fields provided, future `purchase_date` is rejected (both on create and update, and today's date is accepted), non-admins are blocked, unknown ids 404.
- **`test_rentals.py`** — the rent/return state machine: admins rent instantly, regular users get a pending request instead, conflicts on already-in-use/in-repair/unknown hardware, duplicate pending requests are blocked, two different users can hold simultaneous pending requests for the same item, return succeeds/fails correctly (ownership, already-available conflict), `GET /rentals/mine` scoping, and the `GET /hardware` filter/search/sort query params.
- **`test_rental_requests.py`** — the approval workflow: admin-only listing/counting, approving rents the item and marks the request approved, **approving one request auto-rejects every other pending request for the same hardware**, approval fails if the item became unavailable in the meantime (race guard), rejecting, blocking a second decision on an already-decided request, 404 on unknown request id, and `GET /rental-requests/mine` scoping to the caller.
- **`test_search.py`** — semantic search with a mocked Anthropic client (no real API calls): empty/missing query rejected, unauthenticated calls rejected, missing API key and Anthropic errors both return `503`, a successful match returns hardware in the model's returned order, unknown ids from the model are silently dropped, and a regression test asserting `purchase_date` is actually present in the payload sent to the model (the bug described above).
- **`test_seed.py`** — the seeder's `notes`/`history` unification: a `history`-only row folds into `notes`, both present get space-joined, neither present leaves `notes` as `null`.
