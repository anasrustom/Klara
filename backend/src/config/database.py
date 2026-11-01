from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./clm_database.db")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        # Import all models here to register them
        from src.models.user import User
        from src.models.contract import Contract, ContractParty, KeyDate, FinancialTerm
        from src.models.clause import Clause
        from src.models.risk import Risk
        from src.models.chat_history import ChatHistory
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        # create_all never alters existing tables, so add any new columns
        await conn.run_sync(_add_missing_columns)

def _add_missing_columns(sync_conn):
    """
    Lightweight forward migration for SQLite databases created by older versions:
    add every model column the table does not have yet (all new columns are nullable).
    """
    if sync_conn.dialect.name != "sqlite":
        return
    from sqlalchemy import inspect, text
    inspector = inspect(sync_conn)
    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        existing = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing:
                continue
            col_type = column.type.compile(dialect=sync_conn.dialect)
            sync_conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'))
