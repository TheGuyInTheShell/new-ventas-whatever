from typing import Any, Dict, List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db

from core.lib.decorators import Get, Post, Put, Delete
from core.lib.register import Controller
from core.security.shield import Shield
from core.lib.decorators.services import Services

from src.modules.values.services import ValuesService
from src.modules.values.schemas import RQValue, RQValueQuery
from src.modules.values.models import Value


@Shield.register(context="Values API")
@Services(ValuesService)
class ValuesController(Controller):
    ValuesService: ValuesService

    @Post("/")
    @Shield.need(
        name="create.value",
        action="create",
        type="endpoint",
        description="Creates a new value",
    )
    async def create_value(self, payload: RQValue):
        result, error = await self.ValuesService.create_value_with_meta(payload)
        if error:
            return error.to_response()
        return result

    @Post("/query")
    @Shield.need(
        name="query.value",
        action="read",
        type="endpoint",
        description="Query values dynamically",
    )
    async def query_values(self, payload: RQValueQuery):
        filters = {}
        if payload.type:
            filters["type"] = payload.type

        result, error = await self.ValuesService.get_values_paginated(
            page=payload.page,
            page_size=payload.page_size,
            order_by=payload.order_by,
            order=payload.order,
            filters=filters,
            load_meta=payload.meta,
            load_balances=payload.balances,
        )
        if error:
            return error.to_response()
            
        values, total = result
        # Returns raw list of values ensuring JS can parse directly
        return values

    @Delete("/id/{id}")
    @Shield.need(
        name="delete.value",
        action="delete",
        type="endpoint",
        description="Delete a value by internal id",
    )
    async def delete_value(self, id: int, db: AsyncSession = Depends(get_async_db)):
        # Ensuring we return confirmation
        await Value.delete(db, id)
        return {"status": "success", "message": "Value deleted"}
