from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import MetaPerson
from .schemas import (
    RQMetaPerson,
    RSMetaPerson,
    RSMetaPersonList,
)

# prefix /meta
router = APIRouter()

tag = "meta"


@router.get("/id/{id}", response_model=RSMetaPerson, status_code=200, tags=[tag])
async def get_meta(
    id: str | int, db: AsyncSession = Depends(get_async_db)
) -> RSMetaPerson:
    try:
        result = await MetaPerson.find_one(db, id)
        return RSMetaPerson(
            id=result.id,
            uid=result.uid,
            key=result.key,
            value=result.value,
            ref_person=result.ref_person,
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSMetaPersonList, status_code=200, tags=[tag])
async def get_metas(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSMetaPersonList:
    try:
        result = await MetaPerson.find_some(db, pag or 1, ord, status)
        mapped_result = list(map(
            lambda x: RSMetaPerson(
                id=x.id,
                uid=x.uid,
                key=x.key,
                value=x.value,
                ref_person=x.ref_person,
            ),
            result,
        ))
        return RSMetaPersonList(
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


@router.post("/", response_model=RSMetaPerson, status_code=201, tags=[tag])
async def create_meta(
    meta: RQMetaPerson, db: AsyncSession = Depends(get_async_db)
) -> RSMetaPerson:
    try:
        result = await MetaPerson(**meta.model_dump()).save(db)
        return result
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_meta(id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await MetaPerson.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSMetaPerson, status_code=200, tags=[tag])
async def update_meta(
    id: str | int, meta: RQMetaPerson, db: AsyncSession = Depends(get_async_db)
) -> RSMetaPerson:
    try:
        result = await MetaPerson.update(db, id, meta.model_dump())
        return result
    except Exception as e:
        print(e)
        raise e
