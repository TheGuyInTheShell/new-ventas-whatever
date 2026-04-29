from core.lib.register.plugin import Plugin
from core.lib.decorators import Services
from fastapi import FastAPI, Depends
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_injectable import injectable

from src.modules.business_entities.services import BusinessEntitiesService
from src.modules.business_entities.hierarchy.services import (
    BusinessEntitiesHierarchyService,
)
from src.modules.business_entities.schemas import RQBusinessEntity
from src.modules.business_entities.hierarchy.schemas import RQBusinessEntitiesHierarchy


@Services(BusinessEntitiesService, BusinessEntitiesHierarchyService)
class ChineseRestaurant(Plugin):
    BusinessEntitiesService: "BusinessEntitiesService"
    BusinessEntitiesHierarchyService: "BusinessEntitiesHierarchyService"

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    async def init(self):
        await self.initialize_hierarchy()
        print("✅ Chinese Restaurant Plugin initialized")

    @injectable
    async def initialize_hierarchy(self, db: AsyncSession = Depends(get_async_db)):
        # 1. Define entities
        entities = [
            "chinese-restaurant",
            "inventory",
            "menu",
            "tables",
            "bank",
            "desktop_cash",
        ]

        entity_ids = {}
        for name in entities:
            entity = await self.BusinessEntitiesService.get_entity_by_name(name, db=db)
            if not entity:
                entity = await self.BusinessEntitiesService.create_business_entity(
                    RQBusinessEntity(name=name), db=db
                )
            entity_ids[name] = entity.id

        # 2. Define hierarchy relationships (Parent, Child)
        relationships = [
            ("chinese-restaurant", "inventory"),
            ("inventory", "menu"),
            ("chinese-restaurant", "tables"),
            ("chinese-restaurant", "bank"),
            ("chinese-restaurant", "desktop_cash"),
        ]

        for parent_name, child_name in relationships:
            parent_id = entity_ids[parent_name]
            child_id = entity_ids[child_name]

            link = await self.BusinessEntitiesHierarchyService.get_hierarchy_link(
                parent_id, child_id, db=db
            )
            if not link:
                await self.BusinessEntitiesHierarchyService.create_entity_hierarchy(
                    RQBusinessEntitiesHierarchy(
                        ref_entity_top=parent_id, ref_entity_bottom=child_id
                    ),
                    db=db,
                )

        await db.commit()

    async def terminate(self):
        pass
