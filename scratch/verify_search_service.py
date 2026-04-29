import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.modules.business_entities.models import BusinessEntity
from src.modules.business_entities.meta.models import MetaBusinessEntity
from src.modules.business_entities_groups.models import BusinessEntitiesGroup
from src.modules.business_entities_groups.connection.models import BusinessEntitiesGroupConnection
from src.modules.business_entities.hierarchy.models import BusinessEntitiesHierarchy

from src.modules.d.services.business_entities_search_by import BusinessEntitiesSearchByService
from src.modules.d.schemas.business_entities_search_by import RQBusinessEntitiesSearch

DATABASE_URL = "postgresql+asyncpg://postgres:Mf9vEKl7tXbGcdKb3XtlstDBPKFcDW6ljGHjnP2tm4R4CMFGdGbGJ7Bv55Th1rgo@185.194.140.61:5432/postgres"

async def verify_groups_flag():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        service = BusinessEntitiesSearchByService()
        
        print("--- Testing GROUPS Flag (with group filter) ---")
        # First, find a group name
        stmt = select(BusinessEntitiesGroup.name).limit(1)
        res = await db.execute(stmt)
        group_name = res.scalar()
            
        if group_name:
            print(f"Filtering by group: {group_name}")
            query = RQBusinessEntitiesSearch(group_name=group_name, groups=True)
            result, _ = await service.search_business_entities(query, db=db)
            print(f"Entities in group: {result.total}")
            for item in result.data:
                print(f" - {item.name} (Groups: {item.groups})")
        else:
            print("No groups found in DB.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_groups_flag())
