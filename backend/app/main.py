from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .llm import get_llm
from .routers import coach, nutrition, training, users
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

for r in (users.router, nutrition.router, coach.router, training.router):
    app.include_router(r)


@app.get("/health")
def health():
    return {"ok": True, "llm": "anthropic" if get_llm() else "mock"}
