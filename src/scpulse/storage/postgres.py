"""Configuração de conexão com PostgreSQL."""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
import os
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


class Base(DeclarativeBase):
    """Classe base para models SQLAlchemy."""


engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Generator[Session, None, None]:
    """Dependency FastAPI para injetar sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_database() -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP VIEW IF EXISTS v_inventory_risk CASCADE;"))
        conn.execute(
            text("DROP VIEW IF EXISTS v_delays_top_suppliers CASCADE;")
        )
        conn.execute(
            text("DROP VIEW IF EXISTS v_orders_created_daily CASCADE;")
        )

    Base.metadata.drop_all(bind=engine)
    print("🗑️ Todas as tabelas antigas foram apagadas.")

    # Cria todas as tabelas baseadas nos models Python
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas recriadas com sucesso a partir dos models!")


if __name__ == "__main__":
    reset_database()
