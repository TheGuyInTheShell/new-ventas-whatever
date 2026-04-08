from typing import List, Optional, Literal

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators.cache import cache
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.balances.models import Balance
from src.modules.balances.schemas import RQBalance, RSBalance, RSBalanceList
from src.modules.balances.services import create_balance


class BalancesController(Controller):
    """
    Controller for Balances management.
    
    Path: /api/v1/balances
    """

    @Get("/id/{id}", response_model=RSBalance, status_code=200)
    async def get_Balance(
        self, id: str, db: AsyncSession = Depends(get_async_db)
    ) -> RSBalance:
        try:
            result: Balance = await Balance.find_one(db, id)
            return RSBalance(
                id=result.id,
                uid=result.uid,
                currency=result.currency,
                ref_value=result.ref_value,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=List[RSBalance], status_code=200)
    async def get_Balances(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBalanceList:
        try:
            result = await Balance.find_some(db, pag or 1, ord, status) 
            mapped_result = map(
                lambda x: RSBalance(
                    id=x.id,
                    uid=x.uid,
                    currency=x.currency,
                    ref_value=x.ref_value,
                ),
                result,
            )
            return RSBalanceList(
                data=list(mapped_result),
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

    @Post("/", response_model=RSBalance, status_code=201)
    async def create_Balance_endpoint(
        self, balance: RQBalance, db: AsyncSession = Depends(get_async_db)
    ) -> RSBalance:
        try:
            result = await create_balance(db, balance)
            return RSBalance(
                id=result.id,
                uid=result.uid,
                currency=result.currency,
                ref_value=result.ref_value,
            )
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_Balance(self, id: str, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await Balance.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSBalance, status_code=200)
    async def update_Balance(
        self, id: str, balance: RQBalance, db: AsyncSession = Depends(get_async_db)
    ) -> RSBalance:
        try:
            result = await Balance.update(db, id, balance.model_dump())
            return RSBalance(
                id=result.id,
                uid=result.uid,
                currency=result.currency,
                ref_value=result.ref_value,
            )
        except Exception as e:
            print(e)
            raise e
