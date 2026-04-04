from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core import cache

from .models import Balance
from .schemas import RQBalance, RSBalance, RSBalanceList
from .services import create_balance

# prefix /balances
router = APIRouter()

tag = "balances"


@router.get("/id/{id}", response_model=RSBalance, status_code=200, tags=[tag])
async def get_Balance(
    id: str, db: AsyncSession = Depends(get_async_db)
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


@router.get("/", response_model=List[RSBalance], status_code=200, tags=[tag])
async def get_Balances(
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


@router.post("/", response_model=RSBalance, status_code=201, tags=[tag])
async def create_Balance_endpoint(
    balance: RQBalance, db: AsyncSession = Depends(get_async_db)
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


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_Balance(id: str, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await Balance.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSBalance, status_code=200, tags=[tag])
async def update_Balance(
    id: str, balance: RQBalance, db: AsyncSession = Depends(get_async_db)
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
