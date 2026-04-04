from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import MetaBusinessEntity
from .schemas import (
    RQMetaBusinessEntity,
    RSMetaBusinessEntity,
    RSMetaBusinessEntityList,
)

# prefix /meta
router = APIRouter()

tag = "meta"


@router.get("/id/{id}", response_model=RSMetaBusinessEntity, status_code=200, tags=[tag])
async def get_meta(
    id: str | int, db: AsyncSession = Depends(get_async_db)
) -> RSMetaBusinessEntity:
    try:
        result = await MetaBusinessEntity.find_one(db, id)
        return RSMetaBusinessEntity(
            id=result.id,
            uid=result.uid,
            key=result.key,
            value=result.value,
            ref_business_entity=result.ref_business_entity,
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSMetaBusinessEntityList, status_code=200, tags=[tag])
async def get_metas(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSMetaBusinessEntityList:
    try:
        result = await MetaBusinessEntity.find_some(db, pag or 1, ord, status)
        mapped_result = list(map(
            lambda x: RSMetaBusinessEntity(
                id=x.id,
                uid=x.uid,
                key=x.key,
                value=x.value,
                ref_business_entity=x.ref_business_entity,
            ),
            result,
        ))
        return RSMetaBusinessEntityList(
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


@router.post("/", response_model=RSMetaBusinessEntity, status_code=201, tags=[tag])
async def create_meta(
    meta: RQMetaBusinessEntity, db: AsyncSession = Depends(get_async_db)
) -> RSMetaBusinessEntity:
    try:
        result = await MetaBusinessEntity(**meta.model_dump()).save(db)
        return result
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_meta(id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await MetaBusinessEntity.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSMetaBusinessEntity, status_code=200, tags=[tag])
async def update_meta(
    id: str | int, meta: RQMetaBusinessEntity, db: AsyncSession = Depends(get_async_db)
) -> RSMetaBusinessEntity:
    try:
        result = await MetaBusinessEntity.update(db, id, meta.model_dump())
        return result
    except Exception as e:
        print(e)
        raise e
