from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.settings import settings

# SQLite needs special connect_args
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create all tables. Must be called after models are imported."""
    # Import models to register them with Base.metadata
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def ensure_secondary_role_column():
    """Добавить колонку secondary_role в users, если её ещё нет (миграция без Alembic)."""
    with engine.begin() as conn:
        if settings.DATABASE_URL.startswith("sqlite"):
            r = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in r.fetchall()]
            if "secondary_role" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN secondary_role VARCHAR(20)"))
        else:
            # PostgreSQL
            r = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'users' AND column_name = 'secondary_role'"
            ))
            if r.fetchone() is None:
                conn.execute(text("ALTER TABLE users ADD COLUMN secondary_role VARCHAR(20)"))
