from typing import Literal, Optional, List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect as sa_inspect

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.values.models import Value
from src.modules.values.schemas import RQValue, RQValueQuery, RSValue, RSValueList, RSMetaValue, RSBalance
from src.modules.values.services import create_value_with_meta, update_value_with_meta, get_values_paginated
from src.modules.comparison_values.schemas import RSComparisonValue, RSComparisonValueSimple


class ValuesController(Controller):
    """
    Controller for Values management.
    
    Path: /api/v1/values
    """

    def _comparison_to_response(self, comparison) -> RSComparisonValue:
        """Helper to convert ComparisonValue model to response schema"""
        source = None
        target = None

        # Check loaded state to avoid lazy-load in async context
        attrs = sa_inspect(comparison) if hasattr(comparison, '_sa_instance_state') else None
        loaded_keys = attrs.dict if attrs else {}

        if 'source_value' in loaded_keys and comparison.source_value:
            source = RSComparisonValueSimple(
                id=comparison.source_value.id,
                uid=comparison.source_value.uid,
                name=comparison.source_value.name,
                expression=comparison.source_value.expression
            )
        
        if 'target_value' in loaded_keys and comparison.target_value:
            target = RSComparisonValueSimple(
                id=comparison.target_value.id,
                uid=comparison.target_value.uid,
                name=comparison.target_value.name,
                expression=comparison.target_value.expression
            )
        
        return RSComparisonValue(
            uid=comparison.uid,
            id=comparison.id,
            quantity_from=comparison.quantity_from,
            quantity_to=comparison.quantity_to,
            value_from=comparison.value_from,
            value_to=comparison.value_to,
            context=comparison.context,
            source_value=source,
            target_value=target
        )

    def _value_to_response(self, value: Value) -> RSValue:
        """Convert Value model to RSValue response schema"""
        attrs = sa_inspect(value) if hasattr(value, '_sa_instance_state') else None

        meta_list = None
        if attrs and 'meta' in attrs.dict:
            meta_list = [
                RSMetaValue(
                    uid=m.uid,
                    id=m.id,
                    key=m.key,
                    value=m.value
                )
                for m in value.meta if not m.is_deleted
            ]

        comparison_data = None
        if attrs and 'comparisons_from' in attrs.dict and value.comparisons_from:
            comparison_data = self._comparison_to_response(value.comparisons_from[0])

        balances_data = None
        if attrs and 'balances' in attrs.dict and value.balances is not None:
            balances_data = [
                RSBalance(
                    id=b.id,
                    quantity=round(b.quantity, 4),
                    type=b.type 
                )
                for b in value.balances if not b.is_deleted
            ]

        return RSValue(
            uid=value.uid,
            id=value.id,
            name=value.name,
            expression=value.expression,
            type=value.type,
            context=value.context,
            identifier=value.identifier,
            meta=meta_list,
            balances=balances_data,
            comparison=comparison_data
        )

    @Get("/id/{id}", response_model=RSValue, status_code=200)
    async def get_value(
        self,
        id: str, 
        db: AsyncSession = Depends(get_async_db)
    ) -> RSValue:
        """Get a single value by ID or UID"""
        result = await Value.find_one(db, id)
        return self._value_to_response(result)

    @Get("/", response_model=RSValueList, status_code=200)
    async def get_values(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        context: Optional[str] = None,
        type: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSValueList:
        """Get paginated list of values"""
        page = pag or 1
        page_size = 10
        
        filters = {}
        if context:
            filters["context"] = context
        if type:
            filters["type"] = type
        
        values, total = await get_values_paginated(db, page, page_size, "id", ord, filters=filters)
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return RSValueList(
            data=[self._value_to_response(v) for v in values],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_page=page + 1 if page < total_pages else None,
            prev_page=page - 1 if page < total_pages else None,
        )

    @Get("/all", response_model=RSValueList, status_code=200)
    async def get_all_values(
        self,
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSValueList:
        """Get all values without pagination"""
        result = await Value.find_all(db, status)
        
        return RSValueList(
            data=[self._value_to_response(v) for v in result],
            total=len(result),
            page=1,
            page_size=len(result),
            total_pages=1,
            has_next=False,
            has_prev=False,
            next_page=None,
            prev_page=None,
        )

    @Post("/", response_model=RSValue, status_code=201)
    async def create_value(
        self,
        value: RQValue, 
        db: AsyncSession = Depends(get_async_db)
    ) -> RSValue:
        """Create a new value with optional metadata"""
        result = await create_value_with_meta(db, value)
        return self._value_to_response(result)

    @Post("/bulk", response_model=List[RSValue], status_code=201)
    async def create_values_bulk_endpoint(
        self,
        values: List[RQValue],
        db: AsyncSession = Depends(get_async_db)
    ) -> List[RSValue]:
        """Create multiple values in bulk with optional metadata"""
        from src.modules.values.services import create_values_bulk
        results = await create_values_bulk(db, values)
        return [self._value_to_response(v) for v in results]

    @Delete("/id/{id}", status_code=204)
    async def delete_value(
        self,
        id: str, 
        db: AsyncSession = Depends(get_async_db)
    ) -> None:
        """Soft delete a value by ID or UID"""
        await Value.delete(db, id)

    @Put("/id/{id}", response_model=RSValue, status_code=200)
    async def update_value(
        self,
        id: str, 
        value: RQValue, 
        db: AsyncSession = Depends(get_async_db)
    ) -> RSValue:
        """Update a value and its metadata"""
        result = await update_value_with_meta(db, id, value)
        return self._value_to_response(result)

    @Post("/query", response_model=RSValueList, status_code=200)
    async def query_values(
        self,
        query: RQValueQuery,
        db: AsyncSession = Depends(get_async_db)
    ) -> RSValueList:
        """Query values based on filters with optional comparison join"""
        values, total = await Value.query(db, query)

        page = max(query.page, 1)
        page_size = query.page_size
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return RSValueList(
            data=[self._value_to_response(v) for v in values],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_page=page + 1 if page < total_pages else None,
            prev_page=page - 1 if page > 1 else None,
        )
