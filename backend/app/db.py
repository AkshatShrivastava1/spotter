from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

_url = get_settings().db_url
if _url.startswith("sqlite"):
    engine = create_engine(_url, connect_args={"check_same_thread": False})
else:
    # pool_pre_ping: cloud Postgres drops idle connections; reconnect instead of erroring.
    engine = create_engine(_url, pool_pre_ping=True, pool_size=5, max_overflow=5)


def init_db() -> None:
    from . import models  # noqa: F401  (register tables)

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
