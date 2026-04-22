from typing import Any, Dict, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db

from core.lib.decorators import Get, Post, Put, Delete
from core.lib.register import Controller
from core.security.shield import Shield
from core.lib.decorators.services import Services

from src.modules.comparison_values.services import ComparisonValuesService
from src.modules.comparison_values.schemas import RQComparisonValue
from src.modules.comparison_values.models import ComparisonValue


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
    async def get_comparisons(
        self, context: Optional[str] = None, db: AsyncSession = Depends(get_async_db)
    ):
        comparisons, total = (
            await self.ComparisonValuesService.get_comparisons_paginated(
                db, page=1, page_size=1000, context=context
            )
        )
        return {"data": comparisons, "total": total}

    @Post("/")
    @Shield.need(
        name="create.comparison_value",
        action="create",
        type="endpoint",
        description="Creates a new comparison value exchange rate link",
    )
    async def create_comparison(
        self, payload: RQComparisonValue, db: AsyncSession = Depends(get_async_db)
    ):
        return await self.ComparisonValuesService.create_comparison(db, payload)

    @Put("/id/{id}")
    @Shield.need(
        name="update.comparison_value",
        action="update",
        type="endpoint",
        description="Update an existing comparison value rate",
    )
    async def update_comparison(
        self,
        id: str,
        payload: RQComparisonValue,
        db: AsyncSession = Depends(get_async_db),
    ):
        return await self.ComparisonValuesService.update_comparison(db, id, payload)

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
