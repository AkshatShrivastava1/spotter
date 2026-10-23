from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .db import engine, init_db
from .llm import get_llm
from .routers import auth, coach, internal, nutrition, training, users
from .scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    sched = start_scheduler()
    yield
    if sched:
        sched.shutdown(wait=False)


app = FastAPI(title="Spotter API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

for r in (auth.router, users.router, nutrition.router, coach.router, training.router, internal.router):
    app.include_router(r)


@app.get("/health")
def health():
    """Used by the host's health check. Fails loudly if the database is unreachable."""
    with engine.connect() as conn:
        conn.execute(text("select 1"))
    return {"ok": True, "llm": "anthropic" if get_llm() else "mock", "db": engine.dialect.name}
