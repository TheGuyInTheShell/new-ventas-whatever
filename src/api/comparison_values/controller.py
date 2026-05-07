from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db

from core.lib.decorators import Get, Post, Put, Delete
from core.lib.register import Controller
from core.security.shield import Shield
from core.lib.decorators.services import Services

from src.modules.comparison_values.services import ComparisonValuesService
from src.modules.comparison_values.schemas import RQComparisonValue
from src.modules.comparison_values.models import ComparisonValue
from core.lib.http.errors import error_response


@Shield.register(context="Comparison Values API")
@Services(ComparisonValuesService)
class ComparisonValuesController(Controller):
    ComparisonValuesService: ComparisonValuesService

    @Get("/")
    @Shield.need(
        name="read.comparison_value",
        action="read",
        type="endpoint",
        description="Read comparison values filtered by optional context query string",
    )
    async def get_comparisons(self, ref_business_entity: Optional[int] = None):
        result, error = await self.ComparisonValuesService.get_comparisons_paginated(
            page=1, page_size=1000, ref_business_entity=ref_business_entity
        )
        if error:
            raise error_response(error)
        
        if not result:
            return HTTPException(400, "comparisons not found")
        
        comparisons, total = result
        return {"data": comparisons, "total": total}

    @Post("/")
    @Shield.need(
        name="create.comparison_value",
        action="create",
        type="endpoint",
        description="Creates a new comparison value exchange rate link",
    )
    async def create_comparison(self, payload: RQComparisonValue):
        result, error = await self.ComparisonValuesService.create_comparison(payload)
        if error:
            raise error_response(error)
        return result

    @Put("/id/{id}")
    @Shield.need(
        name="update.comparison_value",
        action="update",
        type="endpoint",
        description="Update an existing comparison value rate",
    )
    async def update_comparison(self, id: str, payload: RQComparisonValue):
        result, error = await self.ComparisonValuesService.update_comparison(id, payload)
        if error:
            raise error_response(error)
        return result

    @Delete("/id/{id}")
    @Shield.need(
        name="delete.comparison_value",
        action="delete",
        type="endpoint",
        description="Delete a comparison link",
    )
    async def delete_comparison(
        self, id: str, db: AsyncSession = Depends(get_async_db)
    ):
        await ComparisonValue.delete(db, int(id))
        return {"status": "success", "message": "Comparison deleted"}
