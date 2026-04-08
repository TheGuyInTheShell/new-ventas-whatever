from typing import List, Optional, Literal

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.persons.models import Person
from src.modules.persons.schemas import RQPerson, RSPerson, RSPersonList
from src.modules.persons.services import create_person


class PersonsController(Controller):
    """
    Controller for Persons management.
    
    Path: /api/v1/persons
    """

    @Get("/id/{id}", response_model=RSPerson, status_code=200)
    async def get_Person(
        self, id: str, db: AsyncSession = Depends(get_async_db)
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

    @Get("/", response_model=RSPersonList, status_code=200)
    async def get_Persons(
        self,
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

    @Post("/", response_model=RSPerson, status_code=201)
    async def create_Person_endpoint(
        self, person: RQPerson, db: AsyncSession = Depends(get_async_db)
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

    @Delete("/id/{id}", status_code=204)
    async def delete_Person(self, id: str, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await Person.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSPerson, status_code=200)
    async def update_Person(
        self, id: str, person: RQPerson, db: AsyncSession = Depends(get_async_db)
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
