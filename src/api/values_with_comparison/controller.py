from fastapi.exceptions import HTTPException

from core.lib.http.errors import error_response
from core.lib.decorators import Post, Put
from core.lib.register import Controller
from core.security.shield import Shield
from core.lib.decorators.services import Services

from src.modules.d.schemas.values_with_comparison import (
    RQValueWithComparison,
    QueryValuesWithComparison,
    ResultValueWithComparison,
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
        result, error = (
            await self.DValueWithComparisonService.save_value_with_comparison_service(
                payload
            )
        )
        if error:
            return error_response(error)
        return result

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
        result, error = (
            await self.DValueWithComparisonService.update_value_with_comparison_service(
                id, payload
            )
        )
        if error:
            return error_response(error)
        return result

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
    ) -> ResultValueWithComparison:
        result, error = (
            await self.DValueWithComparisonService.get_values_with_comparison_service(
                payload
            )
        )
        if error:
            exception = error_response(error)
            raise exception
        if not result:
            raise HTTPException(status_code=404, detail="Unexpected error")
        return result
