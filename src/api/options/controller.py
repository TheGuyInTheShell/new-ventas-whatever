from typing import Literal, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.options.models import Options
from src.modules.options.schemas import (
    RQOptions,
    RSOptions,
    RSOptionsList,
)


class OptionsController(Controller):
    """
    Controller for Options management.
    
    Path: /api/v1/options
    """

    @Get("/id/{id}", response_model=RSOptions, status_code=200)
    async def get_options(
        self,
        id: str | int, db: AsyncSession = Depends(get_async_db)
    ) -> RSOptions:
        try:
            result = await Options.find_one(db, id)
            return RSOptions(
                id=result.id,
                uid=result.uid,
                name=result.name,
                context=result.context,
                value=result.value,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSOptionsList, status_code=200)
    async def get_options_list(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        context: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSOptionsList:
        try:
            filters = {}
            if context:
                filters["context"] = context
                
            result = await Options.find_some(db, pag or 1, ord, status, filters=filters)
            mapped_result = list(map(
                lambda x: RSOptions(
                    id=x.id,
                    uid=x.uid,
                    name=x.name,
                    context=x.context,
                    value=x.value,
                ),
                result,
            ))
            return RSOptionsList(
                data=mapped_result,
                total=0,
                page=0,
                page_size=0,
                total_pages=0,
                has_next=False,
                has_prev=False,
                next_page=0,
                prev_page=0,
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/", response_model=RSOptions, status_code=201)
    async def create_options(
        self,
        options: RQOptions, db: AsyncSession = Depends(get_async_db)
    ) -> RSOptions:
        try:
            result = await Options(**options.model_dump()).save(db)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_options(self, id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await Options.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSOptions, status_code=200)
    async def update_options(
        self,
        id: str | int, options: RQOptions, db: AsyncSession = Depends(get_async_db)
    ) -> RSOptions:
        try:
            result = await Options.update(db, id, options.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e
