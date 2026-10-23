from collections.abc import Iterator

from sqlalchemy import inspect, text
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
    _add_missing_columns()


def _add_missing_columns() -> None:
    """Tiny forward-only migration: create_all never alters existing tables, so add new columns
    (nullable, or with a simple default) ourselves. Enough until the schema needs Alembic."""
    insp = inspect(engine)
    with engine.begin() as conn:
        for table in SQLModel.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have or col.primary_key:
                    continue
                ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col.type.compile(dialect=engine.dialect)}'
                if not col.nullable:
                    default = getattr(col.default, "arg", None)
                    if not isinstance(default, (str, int, float, bool)):
                        continue  # can't backfill safely; needs a real migration
                    literal = repr(default) if isinstance(default, str) else str(int(default) if isinstance(default, bool) else default)
                    ddl += f" NOT NULL DEFAULT {literal}"
                conn.execute(text(ddl))
            for idx in table.indexes:
                cols = ", ".join(f'"{c.name}"' for c in idx.columns)
                unique = "UNIQUE " if idx.unique else ""
                conn.execute(text(f'CREATE {unique}INDEX IF NOT EXISTS "{idx.name}" ON "{table.name}" ({cols})'))


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
