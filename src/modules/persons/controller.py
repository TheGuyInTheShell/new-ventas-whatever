from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core import cache

from .models import Person
from .schemas import RQPerson, RSPerson, RSPersonList
from .services import create_person

# prefix /persons
router = APIRouter()

tag = "persons"


@router.get("/id/{id}", response_model=RSPerson, status_code=200, tags=[tag])
async def get_Person(
    id: str, db: AsyncSession = Depends(get_async_db)
) -> RSPerson:
    try:
        result: Person = await Person.find_one(db, id)
        return RSPerson(
            id=result.id,
            uid=result.uid,
            first_names=result.first_names,
            last_names=result.last_names,
            email=result.email,
            identifier=result.identifier,
            type_identifier=result.type_identifier,
            ref_business_entity=result.ref_business_entity
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSPersonList, status_code=200, tags=[tag])
async def get_Persons(
    pag: int = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSPersonList:
    try:
        result = await Person.find_some(db, pag, ord, status)
        mapped_result = list(map(lambda x: RSPerson(
            id=x.id,
            uid=x.uid,
            first_names=x.first_names,
            last_names=x.last_names,
            email=x.email,
            identifier=x.identifier,
            type_identifier=x.type_identifier,
            ref_business_entity=x.ref_business_entity
        ), result))
        return RSPersonList(
            data=mapped_result,
            total=0,
            page=1,
            page_size=10,
            total_pages=1,
            has_next=False,
            has_prev=False,
            next_page=1,
            prev_page=1
        )
    except Exception as e:
        print(e)
        raise e


@router.post("/", response_model=RSPerson, status_code=201, tags=[tag])
async def create_Person_endpoint(
    person: RQPerson, db: AsyncSession = Depends(get_async_db)
) -> RSPerson:
    try:
        result = await create_person(db, person)
        return RSPerson(
            id=result.id,
            uid=result.uid,
            first_names=result.first_names,
            last_names=result.last_names,
            email=result.email,
            identifier=result.identifier,
            type_identifier=result.type_identifier,
            ref_business_entity=result.ref_business_entity
        )
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_Person(id: str, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await Person.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSPerson, status_code=200, tags=[tag])
async def update_Person(
    id: str, person: RQPerson, db: AsyncSession = Depends(get_async_db)
) -> RSPerson:
    try:
        result = await Person.update(db, id, person.model_dump())
        return RSPerson(
            id=result.id,
            uid=result.uid,
            first_names=result.first_names,
            last_names=result.last_names,
            email=result.email,
            identifier=result.identifier,
            type_identifier=result.type_identifier,
            ref_business_entity=result.ref_business_entity
        )
    except Exception as e:
        print(e)
        raise e
