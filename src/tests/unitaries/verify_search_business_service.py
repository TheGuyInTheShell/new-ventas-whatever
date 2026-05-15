import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.modules.business_entities_groups.models import BusinessEntitiesGroup
from src.domain.services.business_entities_hierarchy_groups import (
    BusinessEntitiesSearchByService,
)
from src.domain.schemas.business_entities_hierarchy_groups import (
    RQBusinessEntitiesSearch,
)

from core.config.settings import settings

DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


async def verify_groups_flag():
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

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
            if not result:
                return
            print(f"Entities in group: {result.total}")
            for item in result.data:
                print(f" - {item.name} (Groups: {item.groups})")
        else:
            print("No groups found in DB.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_groups_flag())
