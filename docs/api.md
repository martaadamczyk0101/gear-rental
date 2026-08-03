## API Endpoints

All routes except `POST /auth/login`, `POST /auth/logout`, and `GET /health` require an `X-User-Id` header identifying an existing user (see "Known limitation: MVP auth" above). **Admin** routes additionally require that user to have `is_admin = true`, or they 403.

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/login` | none | Body `{email, password}`. Returns the `UserOut` on success, `401` on bad credentials. |
| `POST` | `/auth/logout` | none | No server-side session to invalidate yet (MVP auth) — just `{"ok": true}`. |
| `GET` | `/auth/me` | any user | Returns the caller's own `UserOut`. |
| `GET` | `/hardware` | any user | List hardware. Query params: `status` (`available`/`in use`/`in repair`), `brand` (substring), `search` (substring on name), `sort_by` (`name`/`brand`/`purchase_date`/`status`, default `name`), `sort_dir` (`asc`/`desc`, default `asc`). |
| `POST` | `/hardware` | admin | Create hardware. Body: `name`, `brand`, `purchase_date?`, `notes?`. Always starts `available`. `422` if `purchase_date` is in the future. |
| `PATCH` | `/hardware/{id}` | admin | Partial update (`name`/`brand`/`purchase_date`/`notes` — only fields present in the body are changed). `404` if not found, `422` on a future `purchase_date`. |
| `PATCH` | `/hardware/{id}/repair-toggle` | admin | Toggles `available` ↔ `in repair`. `409` if the item is currently `in use`. |
| `DELETE` | `/hardware/{id}` | admin | `204` on success. `409` if the item is currently `in use`. |
| `GET` | `/hardware/semantic-search` | any user | Query param `q` (required, non-empty). Sends the full inventory to Claude and returns the matching `HardwareOut` rows. `503` if `ANTHROPIC_API_KEY` isn't set or the Anthropic API errors. |
| `POST` | `/hardware/{id}/rent` | any user | Admin callers rent immediately (`{"outcome": "rented", "hardware": {...}}`). Everyone else gets a pending `RentalRequest` instead (`{"outcome": "requested", ...}`). `409` if the item isn't `available`, or if the caller already has a pending request for it. |
| `POST` | `/hardware/{id}/return` | owner or admin | Returns hardware to `available`. `409` if it isn't currently rented, `403` if you don't own the rental (and aren't an admin). |
| `GET` | `/rentals/mine` | any user | The caller's own open (not yet returned) rentals, with hardware nested. |
| `GET` | `/rental-requests` | admin | Query param `status` (`pending`/`approved`/`rejected`, default `pending`). Lists requests with hardware + requester nested. |
| `GET` | `/rental-requests/pending-count` | admin | `{"pending": N}` — powers the sidebar badge. |
| `GET` | `/rental-requests/mine` | any user | The caller's own pending requests. |
| `POST` | `/rental-requests/{id}/approve` | admin | Rents the item to that requester and auto-rejects every other pending request for the same hardware. `409` if already decided or the item's no longer available. |
| `POST` | `/rental-requests/{id}/reject` | admin | Marks the request rejected. `409` if already decided. |
| `POST` | `/users` | admin | Body: `email`, `password`, `is_admin`. The only way to create an account. `409` on a duplicate email. |
| `GET` | `/health` | none | `{"status": "ok"}` — liveness check. |

