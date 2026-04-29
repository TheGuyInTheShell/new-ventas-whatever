from typing import List, Tuple, Optional
import math

from fastapi import Depends
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_injectable import injectable

from core.database import get_async_db
from core.lib.register.service import Service
from core.lib.decorators.exceptions import handle_service_errors, ServiceResult

from src.modules.business_entities.models import BusinessEntity
from src.modules.business_entities_groups.models import BusinessEntitiesGroup
from src.modules.business_entities_groups.connection.models import (
    BusinessEntitiesGroupConnection,
)
from src.modules.business_entities.hierarchy.models import BusinessEntitiesHierarchy
from src.modules.business_entities.meta.models import (
    MetaBusinessEntity,
)  # Added to fix mapper initialization

from ..schemas.business_entities_search_by import (
    RQBusinessEntitiesSearch,
    RSBusinessEntitiesSearchItem,
    RSBusinessEntitiesSearchList,
)


class BusinessEntitiesSearchByService(Service):

    @handle_service_errors
    @injectable
    async def search_business_entities(
        self, query: RQBusinessEntitiesSearch, db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[RSBusinessEntitiesSearchList]:
        """
        Realiza una búsqueda compleja sobre business entities filtrando por grupos y jerarquía.
        """
        # 1. Base Query
        stmt = select(BusinessEntity).distinct()

        # 2. Joins based on filters
        # If groups=True or group filters are present, we join the groups tables
        if query.groups or query.group_name or query.group_id:
            stmt = stmt.join(
                BusinessEntitiesGroupConnection,
                BusinessEntity.id
                == BusinessEntitiesGroupConnection.ref_business_entities,
            ).join(
                BusinessEntitiesGroup,
                BusinessEntitiesGroupConnection.ref_business_entities_group
                == BusinessEntitiesGroup.id,
            )

        if query.parent_id:
            stmt = stmt.join(
                BusinessEntitiesHierarchy,
                BusinessEntity.id == BusinessEntitiesHierarchy.ref_entity_bottom,
            ).where(BusinessEntitiesHierarchy.ref_entity_top == query.parent_id)

        if query.child_id:
            stmt = stmt.join(
                BusinessEntitiesHierarchy,
                BusinessEntity.id == BusinessEntitiesHierarchy.ref_entity_top,
            ).where(BusinessEntitiesHierarchy.ref_entity_bottom == query.child_id)

        # 3. Apply basic filters (Exact match as requested)
        if query.name:
            stmt = stmt.where(BusinessEntity.name == query.name)

        if query.group_name:
            stmt = stmt.where(BusinessEntitiesGroup.name == query.group_name)

        if query.group_id:
            stmt = stmt.where(BusinessEntitiesGroup.id == query.group_id)

        if query.is_deleted is not None:
            stmt = stmt.where(BusinessEntity.is_deleted == query.is_deleted)

        # 4. Total Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 5. Pagination and Execution
        offset = (query.page - 1) * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)

        result = await db.execute(stmt)
        entities = result.scalars().all()

        # 6. Transform to response items
        data = []
        for entity in entities:
            # Get groups for each entity
            group_stmt = (
                select(BusinessEntitiesGroup.name)
                .join(
                    BusinessEntitiesGroupConnection,
                    BusinessEntitiesGroup.id
                    == BusinessEntitiesGroupConnection.ref_business_entities_group,
                )
                .where(
                    BusinessEntitiesGroupConnection.ref_business_entities == entity.id
                )
            )

            group_res = await db.execute(group_stmt)
            groups = [row[0] for row in group_res.all()]

            # Hierarchy tree building if requested
            children = None
            if query.hierarchy:
                children = await self._get_entity_children(entity.id, db)

            data.append(
                RSBusinessEntitiesSearchItem(
                    id=entity.id,
                    uid=entity.uid,
                    name=entity.name,
                    groups=groups,
                    children=children,
                )
            )

        total_pages = math.ceil(total / query.page_size) if total > 0 else 0

        return (
            RSBusinessEntitiesSearchList(
                data=data,
                total=total,
                page=query.page,
                page_size=query.page_size,
                total_pages=total_pages,
            ),
            None,
        )

    async def _get_entity_children(
        self, parent_id: int, db: AsyncSession
    ) -> List[RSBusinessEntitiesSearchItem]:
        """
        Recursively fetches children to build a hierarchy tree.
        """
        stmt = (
            select(BusinessEntity)
            .join(
                BusinessEntitiesHierarchy,
                BusinessEntity.id == BusinessEntitiesHierarchy.ref_entity_bottom,
            )
            .where(BusinessEntitiesHierarchy.ref_entity_top == parent_id)
        )

        result = await db.execute(stmt)
        children_entities = result.scalars().all()

        children_items = []
        for child in children_entities:
            # Get groups for child
            group_stmt = (
                select(BusinessEntitiesGroup.name)
                .join(
                    BusinessEntitiesGroupConnection,
                    BusinessEntitiesGroup.id
                    == BusinessEntitiesGroupConnection.ref_business_entities_group,
                )
                .where(
                    BusinessEntitiesGroupConnection.ref_business_entities == child.id
                )
            )
            group_res = await db.execute(group_stmt)
            groups = [row[0] for row in group_res.all()]

            # Recursive call for next level of hierarchy
            grand_children = await self._get_entity_children(child.id, db)

            children_items.append(
                RSBusinessEntitiesSearchItem(
                    id=child.id,
                    uid=child.uid,
                    name=child.name,
                    groups=groups,
                    children=grand_children if grand_children else None,
                )
            )

        return children_items
