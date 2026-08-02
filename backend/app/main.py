import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import FRONTEND_ORIGIN
from .routers import auth as auth_router
from .routers import hardware as hardware_router
from .routers import rental_requests as rental_requests_router
from .routers import rentals as rentals_router
from .routers import search as search_router
from .routers import users as users_router
from .seed import run_seed

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Internal Hardware Rental API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(hardware_router.router)
app.include_router(rentals_router.router)
app.include_router(rental_requests_router.router)
app.include_router(search_router.router)
app.include_router(users_router.router)


@app.on_event("startup")
def on_startup():
    run_seed()


@app.get("/health")
def health():
    return {"status": "ok"}
