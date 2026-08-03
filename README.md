# Internal Hardware Rental Tool

**Live demo**: [https://frontend-production-9a9d.up.railway.app/](https://frontend-production-9a9d.up.railway.app/)

An internal tool for tracking company hardware (laptops, phones, headphones, etc.), letting employees rent and return gear, and giving admins a command center to manage the hardware catalog and user accounts.

---

### Fully Implemented

- **Admin command center**: hardware CRUD (create/edit/delete), repair-status toggle, notes, user account creation, everything is guarded against impossible states (can't delete/repair-toggle an item that's `in use`, both server and UI secured)
- **Auth gate**: the only way to get an account is an admin creating one, login screen, route guards redirect unauthenticated users to `/login` and non admins away from `/admin`
- **Dashboard**: hardware list (name/brand/purchase date/status) with search, status/brand filtering, and sortable columns.
- **Rental lifecycle**: rent and return, backed by an atomic conditional `UPDATE ... WHERE status='available'` so a race between two simultaneous rent attempts can't rent the same item to two users at the same time
- **Rental approval workflow**: regular users create a `RentalRequest` instead of an instant rental (admins get instant rent). Approving one request rejects other pending requests for the same item (tested explicitly, including the race case). "My Rentals" + "Pending Requests" show the requester their own state, the admin panel has a Rental Requests queue with a live sidebar badge
- **Semantic search**: `GET /hardware/semantic-search?q=...` sends the full inventory to Claude via structured outputs and returns matching items
- **Data quality pass**: `seed.json` audited row by row, fixable issues (casing, date format) got corrected, unfixable rows (duplicate id, all-null junk row, impossible future date) got dropped and documented, `notes`/`history` fields unified in the seeder so the free text fields are stored in the same place
- **Deployment**: live on Railway (frontend and backend as separate services, backend on a Docker build)

---

### Shortcuts & "Hacks"

#### 1. `X-User-Id` header instead of real sessions/JWT
Instead of implementing full authentication with sessions or JWTs, the application uses a simplified approach. After logging in the frontend receives the user's UserOut object and stores it as JSON in localStorage (frontend/src/stores/auth.js). For subsequent requests, it sends the user's ID in an X-User-Id header. On the backend, backend/app/auth.py::get_current_user reads this header and uses the ID to identify the user. There is no token validation, signature or expiration, so the backend fully trusts the ID provided by the client.

- **The "Why"**: This was a shortcut that made authentication quick to implement, it exists to get the full workflow (admin CRUD, rent/return, filtering) working end-to-end quickly
- **The "Future"**: replace with server-side sessions (signed, httpOnly cookie) or JWT with short expiry + refresh. Easy to forge right now as anyone can set `X-User-Id: 1` in a request and impersonate the admin without credentials. This is highest priority for now

#### 2. Semantic search sends the whole inventory on every call, no embeddings/vector DB
`backend/app/llm.py` sends the entire hardware table (id/name/brand/notes/status/purchase_date) as JSON in the prompt on every search request, one live Claude call per query.

- **The "Why"**: the inventory is small for now, so it doesn'y affect the usage and costs, the search gets correct answers with less code and no extra infrastructure.
- **The "Future"**: if the catalog grows into the thousands of items or query volume gets too high enough, then move to embeddings + a vector index (or at least cache or paginate the inventory payload)

#### 3. Brand and device name are free-text strings
Discussed with the model (typos like "Appel" were found and fixed during the data-quality pass) but the enum/combobox + "add new brand" or "add new device" wasn't built. `brand` and 'device_name' are plain strings columns and have no validation

- **The "Why"**: typo risk is low damage for fields that only admins can fill on an internal tool.
- **The "Future"**: the real fix is to us a relational database. Put `brand` into `brands(id, name UNIQUE)` table with `hardware.brand_id` as a foreign key, and do the same for `device_name` with a `device_models(id, name UNIQUE)` table + `hardware.device_model_id`. This way a typo like "Appel" can't be written to either column. The admin UI would still need a picker + "+ Add new brand" and "+ Add new device" buttons and `POST /brands` and `POST /device-models` endpoints

#### 4. Rental-request badge polls every 25s instead of push
The rental request badge checks the backend every 25 seconds to see if there are any new pending requests (frontend/src/stores/rentalRequestBadge.js). Instead of using WebSockets to receive updates immediately, the frontend sends a `GET /rental-requests/pending-count` request every 25 seconds.

- **The "Why"**: this was chosen as a simple solution because there was no WebSocket infrastructure, and a max delay of 25 seconds is acceptable for this application
- **The "Future"**: if real time updates are necessary in the future, this could be replaced with WebSockets

---

### Partial or Missing

- **No password reset or account recovery flow.** Admin sets a password directly on user creation and there's no "forgot password" path, a locked-out user needs an admin to intervene manually (no rotate-password endpoint exists either, so today that means direct DB access)
- **No pagination** on `/hardware` or `/rental-requests` listing endpoints, fine at current inventory size, will need it if the catalog grows large
- **No rate limiting** on `/auth/login` or the semantic-search endpoint (the search is a billed external call, so an unrate-limited loop is also a cost control gap, not just a security one)

---

### Next Steps (The 24h Roadmap)

If given one more day, in this priority order, I would:

1. **Replace `X-User-Id` with real sessions.** This is the one item that actually blocks calling the app production ready, right now, it's easy to forge by anyone who can see a request. Signed httpOnly session cookie is the smallest correct fix, JWT is the alternative if a stateless backend becomes a requirement later.
2. **Normalize `brand` and `device_name` into their own tables with foreign keys**, plus the admin picker/"+ Add new" buttons, motivated by a real data quality bug that was found and fixed. This prevents that class of typo at the schema level instead of relying on manual audits.
3. **Add minimal rate limiting**: `/auth/login` (brute-force) and `/hardware/semantic-search` (billed Claude calls, currently uncapped per user). A simple in-memory or Redis-backed limiter plus a Sentry (or similar) hook on the backend would close the biggest blind spots.

