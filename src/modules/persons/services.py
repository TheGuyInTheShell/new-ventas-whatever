from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import Person
from .schemas import RQPerson

class PersonsService(Service):
    @injectable
    async def create_person(
        self,
        person_data: RQPerson,
        db: AsyncSession = Depends(get_async_db),
    ) -> Person:
        person = Person(
            first_names=person_data.first_names,
            last_names=person_data.last_names,
            email=person_data.email,
            identifier=person_data.identifier,
            type_identifier=person_data.type_identifier,
            ref_business_entity=person_data.ref_business_entity
        )
        await person.save(db)
        return person

