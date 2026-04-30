import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.modules.business_entities.models import BusinessEntity
from src.modules.business_entities.meta.models import MetaBusinessEntity # Fix mapper
from src.modules.business_entities.hierarchy.models import BusinessEntitiesHierarchy

DATABASE_URL = "postgresql+asyncpg://postgres:Mf9vEKl7tXbGcdKb3XtlstDBPKFcDW6ljGHjnP2tm4R4CMFGdGbGJ7Bv55Th1rgo@185.194.140.61:5432/postgres"

async def check_hierarchy():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Find 'chinese-restaurant'
        stmt = select(BusinessEntity).where(BusinessEntity.name == 'chinese-restaurant')
        res = await db.execute(stmt)
        parent = res.scalar_one_or_none()
        
        if not parent:
            print("Parent 'chinese-restaurant' not found")
            return
            
        print(f"Parent found: {parent.name} (ID: {parent.id})")
        
        # Find its children
        stmt = select(BusinessEntity).join(
            BusinessEntitiesHierarchy, BusinessEntity.id == BusinessEntitiesHierarchy.ref_entity_bottom
        ).where(BusinessEntitiesHierarchy.ref_entity_top == parent.id)
        
        res = await db.execute(stmt)
        children = res.scalars().all()
        
        print(f"Children found ({len(children)}):")
        for child in children:
            print(f" - {child.name} (ID: {child.id})")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_hierarchy())
