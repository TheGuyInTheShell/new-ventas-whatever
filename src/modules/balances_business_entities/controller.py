from typing import List, Optional, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import BalanceBusinessEntity
from .schemas import (
    RQBalanceBusinessEntity,
    RSBalanceBusinessEntity,
    RSBalanceBusinessEntityList,
)
from .services import create_balance_business_entity

# prefix /balances_business_entities
router = APIRouter()

tag = "balances_business_entities"


@router.get("/id/{id}", response_model=RSBalanceBusinessEntity, status_code=200, tags=[tag])
async def get_BalanceBusinessEntity(
    id: str, db: AsyncSession = Depends(get_async_db)
) -> RSBalanceBusinessEntity:
    try:
        result = await BalanceBusinessEntity.find_one(db, id)
        return RSBalanceBusinessEntity(
            id=result.id, uid=result.uid,
            ref_business_entity=result.ref_business_entity,
            ref_balance=result.ref_balance,
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSBalanceBusinessEntityList, status_code=200, tags=[tag])
async def get_BalanceBusinessEntities(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSBalanceBusinessEntityList:
    try:
        result = await BalanceBusinessEntity.find_some(db, pag or 1, ord=ord, status=status)
        mapped_result = [
            RSBalanceBusinessEntity(
                id=x.id, uid=x.uid,
                ref_business_entity=x.ref_business_entity,
                ref_balance=x.ref_balance,
            )
            for x in result
        ]
        return RSBalanceBusinessEntityList(
            data=mapped_result,
            total=0, page=0, page_size=0, total_pages=0,
            has_next=False, has_prev=False, next_page=0, prev_page=0,
        )
    except Exception as e:
        print(e)
        raise e


@router.post("/", response_model=RSBalanceBusinessEntity, status_code=201, tags=[tag])
async def create_BalanceBusinessEntity_endpoint(
    data: RQBalanceBusinessEntity, db: AsyncSession = Depends(get_async_db)
) -> RSBalanceBusinessEntity:
    try:
        result = await create_balance_business_entity(db, data)
        return RSBalanceBusinessEntity(
            id=result.id, uid=result.uid,
            ref_business_entity=result.ref_business_entity,
            ref_balance=result.ref_balance,
        )
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_BalanceBusinessEntity(
    id: str, db: AsyncSession = Depends(get_async_db)
) -> None:
    try:
        await BalanceBusinessEntity.delete(db, id)
    except Exception as e:
        print(e)
        raise e
