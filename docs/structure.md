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
        hardware.py            # hardware CRUD, repair-toggle, general edit (admin) + filtered/sorted list (any user)
        rentals.py              # rent/return (atomic status guard, admin-vs-user branching) + my-rentals
        rental_requests.py        # request/approve/reject workflow (list, pending-count, mine)
        search.py                # /hardware/semantic-search (LLM natural-language search)
        users.py                # admin-only user creation
    tests/                        # pytest suite for the rental state machine, approval workflow, filters/sort, and semantic search
    requirements.txt
    .env.example                    # template for local secrets (copy to .env, gitignored)
    Dockerfile                        # builds from the repo root as context - see "Deploying to Railway"
  frontend/
    src/
      main.js, App.vue
      api/client.js            # fetch wrapper, attaches X-User-Id
      stores/{auth.js, toast.js, rentalRequestBadge.js}  # Pinia stores: auth, global toasts, admin sidebar badge
      router/index.js            # routes + auth/admin guards
      components/{StatusBadge.vue, Modal.vue, HardwareFormModal.vue, UserFormModal.vue, ToastContainer.vue}
      views/
        LoginView.vue, DashboardView.vue, MyRentalsView.vue, AdminView.vue
    package.json
  seed.json
  PLAN.md
  README.md
  .dockerignore                       # scoped to the backend Docker build (repo-root context)
```
