from core.config.settings import settings
import time

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

DB_USER = str(settings.DB_USER).strip()
DB_PASSWORD = str(settings.DB_PASSWORD).strip()
DB_HOST = str(settings.DB_HOST).strip()
DB_PORT = str(settings.DB_PORT).strip()
DB_NAME = str(settings.DB_NAME).strip()
DEBUG = settings.MODE == "DEVELOPMENT"

# SQLALCHEMY
engineAsync = None


def init_async_engine():
    global engineAsync
    while engineAsync is None:
        try:
            engineAsync = create_async_engine(
                url=f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
                echo=DEBUG,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                query_cache_size=1200,
                pool_recycle=1800,
                pool_use_lifo=True,
            )
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("try")
            print(e)
            time.sleep(10)


init_async_engine()

SessionAsync = async_sessionmaker(engineAsync)


async def get_async_db():
    db = SessionAsync()
    try:
        yield db
    finally:
        await db.close()


async def warm_up_async_db():
    """
    Establishes the initial connection to the database to avoid
    the ~1.5s overhead on the first user request.
    """
    from sqlalchemy import text

    if engineAsync is not None:
        async with engineAsync.connect() as conn:
            await conn.execute(text("SELECT 1"))
    else:
        print("engineAsync is None")
