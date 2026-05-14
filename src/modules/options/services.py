from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.lib.register.service import Service
from .models import Options
from .schemas import Option
from fastapi import Depends
from core.database import get_async_db
from fastapi_injectable import injectable
from typing import Optional


class OptionsService(Service):

    @injectable
    async def create_options(
        self,
        name: str,
        context: str,
        value: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> Option:
        """
        Create a new options in the database.

        Args:
            name: Name of the options
            context: Context of the options
            value: Value of the options
            db: Database session -> its injected by fastapi-injectable

        Returns:
            Option: The created options
        """
        options_obj = Options(
            name=name,
            context=context,
            value=value,
        )
        await options_obj.save(db)
        await db.refresh(options_obj)
        return Option(
            id=options_obj.id,
            uid=options_obj.uid,
            name=options_obj.name,
            context=options_obj.context,
            value=options_obj.value,
        )

    @injectable
    async def get_option(
        self,
        context: str,
        name: str,
        value: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> Optional[Option]:
        """
        Query an option in the database.

        Args:
            context: Context of the option
            name: Name of the option
            value: Value of the option
            db: Database session -> its injected by fastapi-injectable

        Returns:
            Optional[Option]: The option if exists, None otherwise
        """
        stmt = select(Options).where(
            Options.context == context,
            Options.name == name,
            Options.value == value,
        )
        result = await db.execute(stmt)
        options_obj = result.scalar_one_or_none()
        if options_obj:
            return Option(
                id=options_obj.id,
                uid=options_obj.uid,
                name=options_obj.name,
                context=options_obj.context,
                value=options_obj.value,
            )
        return None
