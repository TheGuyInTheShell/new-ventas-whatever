import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://postgres:Mf9vEKl7tXbGcdKb3XtlstDBPKFcDW6ljGHjnP2tm4R4CMFGdGbGJ7Bv55Th1rgo@185.194.140.61:5432/postgres"

async def check_global():
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name FROM business_entities WHERE name = 'global'"))
        row = res.fetchone()
        
        if row:
            print(f"FOUND: {row[1]} (ID: {row[0]})")
        else:
            print("NOT FOUND: 'global'")
            
        res = await conn.execute(text("SELECT id, name FROM business_entities WHERE name = 'chinese-restaurant'"))
        row = res.fetchone()
        if row:
            print(f"FOUND: {row[1]} (ID: {row[0]})")
        else:
            print("NOT FOUND: 'chinese-restaurant'")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_global())
