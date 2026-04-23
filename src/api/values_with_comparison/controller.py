from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db

from core.lib.decorators import Get, Post, Put
from core.lib.register import Controller
from core.security.shield import Shield
from core.lib.decorators.services import Services

from src.modules.d.schemas.values_with_comparison import (
    RQValueWithComparison,
    QueryValuesWithComparison,
)
from src.modules.d.services.value_with_comparison import DValueWithComparisonService


@Shield.register(context="Values With Comparison API")
@Services(DValueWithComparisonService)
class ValuesWithComparisonController(Controller):
    DValueWithComparisonService: DValueWithComparisonService

    @Post("/")
    @Shield.need(
        name="create.value_with_comparison",
        action="create",
        type="endpoint",
        description="Save an optional value and an optional comparison.",
    )
    async def create_value_with_comparison(self, payload: RQValueWithComparison):
        return (
            await self.DValueWithComparisonService.save_value_with_comparison_service(
                payload
            )
        )

    @Put("/id/{id}")
    @Shield.need(
        name="update.value_with_comparison",
        action="update",
        type="endpoint",
        description="Update a value with its comparison.",
    )
    async def update_value_with_comparison(
        self,
        id: str,
        payload: RQValueWithComparison,
    ):
        return (
            await self.DValueWithComparisonService.update_value_with_comparison_service(
                id, payload
            )
        )

    @Post("/query")
    @Shield.need(
        name="query.value_with_comparison",
        action="read",
        type="endpoint",
        description="Get all values with their comparisons using filters",
    )
    async def query_values_with_comparison(
        self,
        payload: QueryValuesWithComparison,
    ):
        return (
            await self.DValueWithComparisonService.get_values_with_comparison_service(
                payload
            )
        )
