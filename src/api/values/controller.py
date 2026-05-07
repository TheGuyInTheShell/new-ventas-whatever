from fastapi.exceptions import HTTPException
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db

from core.lib.decorators import Get, Post, Put, Delete
from core.lib.register import Controller
from core.security.shield import Shield
from core.lib.decorators.services import Services

from src.modules.values.services import ValuesService
from src.modules.values.schemas import RQValue, RQValueQuery, RSValue, RSValueList
from core.lib.http.errors import error_response


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
    async def create_value(self, payload: RQValue) -> RSValue:
        result, error = await self.ValuesService.create_value_with_meta(payload)
        if error:
            raise error_response(error)
        if not result:
            raise HTTPException(detail={"message": "Unknown error", "code": "Somethin happend" }, status_code=500)
        return result

    @Post("/query")
    @Shield.need(
        name="query.value",
        action="read",
        type="endpoint",
        description="Query values dynamically",
    )
    async def query_values(self, payload: RQValueQuery) -> RSValueList:
        result, error = await self.ValuesService.get_values_paginated(payload)
        if error:
            raise error_response(error)
        if not result:
            raise HTTPException(detail={"message": "Unknown error", "code": "Somethin happend" }, status_code=500)
        return result

    @Delete("/id/{id}")
    @Shield.need(
        name="delete.value",
        action="delete",
        type="endpoint",
        description="Delete a value by internal id",
    )
    async def delete_value(self, id: int):
        # Ensuring we return confirmation
        result, error = await self.ValuesService.delete_value(id)
        if error:
            raise error_response(error)
        return {"code": "success", "message": "Value deleted"}
