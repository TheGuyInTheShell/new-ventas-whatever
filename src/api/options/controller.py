from typing import Any, Dict, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db

from core.lib.decorators import Get, Post, Put, Delete
from core.lib.register import Controller
from core.security.shield import Shield
from core.lib.decorators.services import Services

from src.modules.options.services import OptionsService
from src.modules.options.schemas import CreateOption
from src.modules.options.models import Options


@Shield.register(context="Options API")
@Services(OptionsService)
class OptionsController(Controller):
    OptionsService: OptionsService

    @Get("/")
    @Shield.need(
        name="read.option",
        action="read",
        type="endpoint",
        description="Fetch options by context, commonly used to get main_fiat_currency.",
    )
    async def get_options(
        self, context: Optional[str] = None, db: AsyncSession = Depends(get_async_db)
    ):
        filters = {}
        if context:
            filters["context"] = context

        options_list = await Options.find_all(db, status="exists", filters=filters)
        return options_list

    @Post("/")
    @Shield.need(
        name="create.option",
        action="create",
        type="endpoint",
        description="Store a new platform option (e.g., main_fiat_currency)",
    )
    async def create_option(
        self, payload: CreateOption
    ):
        return await self.OptionsService.create_options(
            payload.name, payload.context, payload.value
        )

    @Put("/id/{id}")
    @Shield.need(
        name="update.option",
        action="update",
        type="endpoint",
        description="Update an existing platform option",
    )
    async def update_option(
        self, id: str, payload: CreateOption, db: AsyncSession = Depends(get_async_db)
    ):
        update_data = {
            "name": payload.name,
            "context": payload.context,
            "value": payload.value,
        }
        await Options.update(db, int(id), update_data)
        return await Options.find_one(db, id)
