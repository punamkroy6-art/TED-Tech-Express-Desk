from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from redis.asyncio import Redis, from_url
from app.config import settings

# Detect if we should use local mocks for zero-admin execution
USE_LOCAL_MOCK = settings.use_local_mock

# Database setup
if USE_LOCAL_MOCK:
    # Use SQLite for local development (zero-install)
    database_url = "sqlite+aiosqlite:///./ted.db"
    engine = create_async_engine(database_url, echo=True, future=True)
else:
    # Use standard PostgreSQL
    engine = create_async_engine(settings.database_url, echo=True, future=True)

# Create asynchronous session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for declarative ORM models
Base = declarative_base()

# Async dependency to get db session in FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Database initialization (creates metadata tables)
async def init_db():
    async with engine.begin() as conn:
        # Import models inside function to avoid circular imports during startup
        import app.models.employee
        import app.models.session
        import app.models.diagnosis
        import app.models.error_pattern
        import app.models.audit_log
        await conn.run_sync(Base.metadata.create_all)

# Async Redis client helper (standard Redis or in-memory Fakeredis)
async def get_redis() -> Redis:
    if USE_LOCAL_MOCK:
        import fakeredis.aioredis
        # Return a singleton-like FakeRedis instance
        if not hasattr(get_redis, "_fake_redis"):
            get_redis._fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        return get_redis._fake_redis
    else:
        return from_url(settings.redis_url, decode_responses=True)
