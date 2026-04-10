import asyncio
import uuid
from datetime import datetime
from functools import wraps
import json
from typing import Any, List, Literal, Self, Sequence, Set, Union

from sqlalchemy import (
    TIMESTAMP,
    UUID,
    Boolean,
    Column,
    ColumnElement,
    Integer,
    String,
    Table,
    desc,
    func,
    select,
    text,
    update,
    Row,
)

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, ProgrammingError, DataError


from sqlalchemy_utils import create_view, get_mapper # type: ignore

from sqlalchemy import MetaData

from .async_connection import SessionAsync

from .sync_connection import SessionSync

from core.database.exceptions import DatabaseError, DatabaseConnectionError, DatabaseQueryError, DatabaseIntegrityError, DatabaseDataError, DatabaseOperationalError, DatabaseProgrammingError # type: ignore

from .async_connection import engineAsync

from .sync_connection import engineSync


from .async_connection import get_async_db

from .sync_connection import get_sync_db



def generate_uuid():

    return str(uuid.uuid4())


def generate_dll_view(tablename: str, is_deleted: str) -> str:

    return f"""

            CREATE OR REPLACE VIEW {tablename}_{'deleted' if is_deleted == 'true' else 'exists'} AS

            SELECT *

            FROM {tablename}

            WHERE is_deleted = {is_deleted};

            """


class VanillaBaseAsync(DeclarativeBase):
    pass


class BasicBaseAsync(DeclarativeBase):
    uid: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
        primary_key=True,
        default=generate_uuid,
    )

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, nullable=False, autoincrement=True, unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp()
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.now(), onupdate=func.current_timestamp()
    )

    deleted_at: Mapped[datetime] = mapped_column(nullable=True)

    is_deleted: Mapped[bool] = mapped_column(default=False)

    @classmethod
    def apply_rls_and_indexes(cls) -> None:
        def create(model_cls: type[Self]):
            try:
                table_name = getattr(model_cls, "__tablename__", None)
                if not table_name:
                    return

                sync_conn = SessionSync()
                
                # Enable Row Level Security (RLS)
                sync_conn.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"))
                
                # Drop policy if exists to recreate
                sync_conn.execute(text(f"DROP POLICY IF EXISTS {table_name}_active_policy ON {table_name};"))
                
                # Create Policy for SELECT ensuring deleted_at IS NULL
                sync_conn.execute(text(f"""
                    CREATE POLICY {table_name}_active_policy ON {table_name}
                    FOR SELECT
                    USING (deleted_at IS NULL);
                """))
                
                # Create Partial Index (Crucial for performance optimization)
                sync_conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_active
                    ON {table_name} (id) 
                    WHERE deleted_at IS NULL;
                """))
                
                sync_conn.commit()
                sync_conn.close()
            except Exception as e:
                pass # Suppress warning spam when running alembic auto-generator

        import threading
        threading.Thread(target=create, args=(cls,), daemon=True).start()

    def __init_subclass__(cls) -> None:
        cls.apply_rls_and_indexes()
        super().__init_subclass__()

    @classmethod
    async def count(cls, db: AsyncSession, status: Literal["exists", "deleted", "all"] = "exists") -> int:
        try:
            query = select(func.count()).select_from(cls)
            
            if status == "exists":
                query = query.where(cls.deleted_at.is_(None))
            elif status == "deleted":
                query = query.where(cls.deleted_at.is_not(None))
            elif status == "all":
                pass
            else:
                raise DatabaseQueryError("Invalid status")
                
            result = (await db.execute(query)).scalar()
            return int(result) if result is not None else 0
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))

    async def save(self, db: AsyncSession) -> Self:
        try:
            db.add(self)
            await db.commit()
            await db.refresh(self)
            return self
        except IntegrityError as e:
            await db.rollback()
            raise DatabaseIntegrityError(str(e))
        except OperationalError as e:
            await db.rollback()
            raise DatabaseOperationalError(str(e))
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(str(e))

    @classmethod
    async def delete(cls, db: AsyncSession, id: int | str):
        reg = await cls.find_one(db, id)

        if reg is None or reg.is_deleted:
            raise DatabaseQueryError(f"No exists the register {cls.__tablename__}")

        is_deleted = True
        deleted_at = datetime.now()
        data = {"is_deleted": is_deleted, "deleted_at": deleted_at}

        try:
            try:
                val_id = int(str(id))
                query = update(cls).where(cls.id == val_id).values(**data)
            except ValueError:
                query = update(cls).where(cls.uid == id).values(**data)

            await db.execute(query)
            await db.commit()
            
            # Update memory object since db.refresh(reg) might fail with RLS enabled
            reg.is_deleted = is_deleted
            reg.deleted_at = deleted_at

            return reg
        except IntegrityError as e:
            await db.rollback()
            raise DatabaseIntegrityError(str(e))
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(str(e))

    @classmethod
    async def update(cls, db: AsyncSession, id: int | str, data: dict):
        updated_at = datetime.now()
        data.update({"updated_at": updated_at})

        reg = await cls.find_one(db, id)

        if reg is None or reg.is_deleted:
            raise DatabaseQueryError(f"No exists the register in {cls.__tablename__}")

        try:
            try:
                val_id = int(str(id))
                query = update(cls).where(cls.id == val_id).values(**data)
            except ValueError:
                query = update(cls).where(cls.uid == id).values(**data)

            await db.execute(query)
            await db.commit()
            await db.refresh(reg)

            return reg
        except IntegrityError as e:
            await db.rollback()
            raise DatabaseIntegrityError(str(e))
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(str(e))

    @classmethod
    async def find_one(cls, db: AsyncSession, id: Union[int, str]) -> Self:
        try:
            try:
                val_id = int(str(id))
                query = select(cls).where(cls.id == val_id)
            except ValueError:
                query = select(cls).where(cls.uid == id)

            result = (await db.execute(query)).scalar_one_or_none()

            if result is None:
                raise DatabaseQueryError(f"Not exists the register in {cls.__tablename__}")

            if result.is_deleted:
                raise DatabaseQueryError(f"The register {cls.__tablename__} is deleted")
            return result
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))

    @classmethod
    async def find_all(
        cls,
        db: AsyncSession,
        status: Literal["deleted", "exists", "all"] = "all",
        filters: dict = dict(),
    ) -> List[Self]:
        try:
            query = select(cls).filter_by(**filters)

            if status == "deleted":
                query = query.where(cls.deleted_at.is_not(None))
            elif status == "exists":
                query = query.where(cls.deleted_at.is_(None))

            result = (await db.execute(query)).scalars().all()
            return list(result)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))

    @classmethod
    def get_order_by(cls, order_by: str) -> Column | None:
        table = Table(cls.__tablename__, MetaData(), autoload_with=engineSync)
        return table.c.get(order_by)

    @classmethod
    async def find_some(
        cls,
        db: AsyncSession,
        pag: int = 1,
        order_by: str = "id",
        ord: str = "asc",
        status: Literal["deleted", "exists", "all"] = "all",
        filters: dict = {},
    ) -> List[Self]:
        try:
            query = select(cls).filter_by(**filters)

            if status == "deleted":
                query = query.where(cls.deleted_at.is_not(None))
            elif status == "exists":
                query = query.where(cls.deleted_at.is_(None))

            order_column = getattr(cls, order_by, None)
            if order_column is None:
                order_column = cls.id

            if ord == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

            if pag <= 0:
                pag = 1

            query = query.limit(10).offset((pag - 1) * 10)

            result = (await db.execute(query)).scalars().all()
            return list(result)
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))

    @classmethod
    async def find_by_colunm(cls, db: AsyncSession, column: str, value: Any):
        try:
            result = await db.execute(select(cls).where(getattr(cls, column) == value))
            return result
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))

    @classmethod
    async def find_by_specification(cls, db: AsyncSession, specification: dict):
        try:
            result = await db.execute(select(cls).where(**specification))
            return result
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))



class BaseAsync(DeclarativeBase):

    uid: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
        primary_key=True,
        default=generate_uuid,
    )

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, nullable=False, autoincrement=True, unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.current_timestamp()
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=func.now(), onupdate=func.current_timestamp()
    )

    deleted_at: Mapped[datetime] = mapped_column(nullable=True)

    is_deleted: Mapped[bool] = mapped_column(default=False)

    @classmethod
    async def count(cls, db: AsyncSession, status: Literal["exists", "deleted", "all"] = "exists") -> int:
        try:
            query = select(func.count())
            
            if status == "exists":
                query = query.select_from(cls.get_exists())
            elif status == "deleted":
                query = query.select_from(cls.get_deleted())
            elif status == "all":
                query = query.select_from(cls)
            else:
                raise DatabaseQueryError("Invalid status")
                
            result = (await db.execute(query)).scalar()
            return int(result) if result is not None else 0
        except Exception as e:
            raise DatabaseQueryError(str(e))

    @classmethod
    def get_deleted(cls) -> Table:
        return cls.deleted # type: ignore

    @classmethod
    def get_exists(cls) -> Table:

        return cls.exists # type: ignore

    @classmethod
    def touple_to_dict(cls, arr: Sequence[Self]) -> List[Self]:

        mapped = get_mapper(cls)

        result = []

        for touple in arr:

            obj = cls()
            colums = mapped.columns

            for i, column in enumerate(colums):

                obj.__setattr__(column.name, touple[i]) # type: ignore

            result.append(obj)
        return result

    async def save(self, db: AsyncSession):
        try:
            db.add(self)

            await db.commit()

            await db.refresh(self)
            return self
        except IntegrityError as e:
            await db.rollback()
            raise DatabaseIntegrityError(str(e))
        except OperationalError as e:
            await db.rollback()
            raise DatabaseOperationalError(str(e))
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(str(e))

    @classmethod
    def create_global_views(cls):

        def create(model_cls: type[Self]):
            try:
                sync_conn = SessionSync()

                sync_conn.execute(text(generate_dll_view(model_cls.__tablename__, "true")))

                sync_conn.execute(text(generate_dll_view(model_cls.__tablename__, "false")))

                sync_conn.commit()

                model_cls.deleted = create_view(
                    name=f"{model_cls.__tablename__}_deleted",
                    selectable=select(model_cls).where(model_cls.is_deleted == True),
                    metadata=BaseAsync.metadata,
                )

                model_cls.exists = create_view(
                    name=f"{model_cls.__tablename__}_exists",
                    selectable=select(model_cls).where(model_cls.is_deleted == False),
                    metadata=BaseAsync.metadata,
                )

                sync_conn.close()
            except Exception as e:
                pass

        import threading
        threading.Thread(target=create, args=(cls,), daemon=True).start()

    def __init_subclass__(cls) -> None:

        cls.create_global_views()

        return super().__init_subclass__()

    @classmethod
    async def delete(cls, db: AsyncSession, id: int | str):

        reg = await cls.find_one(db, id)

        if reg is None or reg.is_deleted:

            raise DatabaseQueryError(f"No exists the register {cls.__tablename__}")

        is_deleted = True

        deleted_at = datetime.now()

        data = {"is_deleted": is_deleted, "deleted_at": deleted_at}

        try:
            try:
                val_id = int(str(id))
                query = update(cls).where(cls.id == val_id).values(**data)
            except ValueError:
                query = update(cls).where(cls.uid == id).values(**data)

            await db.execute(query)

            await db.commit()

            await db.refresh(reg)

            return reg
        except IntegrityError as e:
            await db.rollback()
            raise DatabaseIntegrityError(str(e))
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(str(e))

    @classmethod
    async def update(cls, db: AsyncSession, id: int | str, data: dict):

        updated_at = datetime.now()

        data.update({"updated_at": updated_at})

        reg = await cls.find_one(db, id)

        if reg is None or reg.is_deleted:

            raise DatabaseQueryError(f"No exists the register in {cls.__tablename__}")

        try:
            try:
                val_id = int(str(id))
                query = update(cls).where(cls.id == val_id).values(**data)
            except ValueError:
                query = update(cls).where(cls.uid == id).values(**data)

            await db.execute(query)

            await db.commit()

            await db.refresh(reg)

            return reg
        except IntegrityError as e:
            await db.rollback()
            raise DatabaseIntegrityError(str(e))
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(str(e))

    @classmethod
    async def find_one(cls, db: AsyncSession, id: Union[int, str]) -> Self:

        try:
            try:
                val_id = int(str(id))
                query = select(cls).where(cls.id == val_id)
            except ValueError:
                query = select(cls).where(cls.uid == id)

            result = (await db.execute(query)).scalar_one_or_none()

            if result is None:

                raise DatabaseQueryError(f"Not exists the register in {cls.__tablename__}")

            if result.is_deleted:

                raise DatabaseQueryError(f"The register {cls.__tablename__} is deleted")
            return result
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))

    @classmethod
    async def find_all(
        cls,
        db: AsyncSession,
        status: Literal["deleted", "exists", "all"] = "all",
        filters: dict = dict(),
    ) -> List[Self]:
        try:
            base_query = select(cls).filter_by(**filters)

            if status == "deleted":

                base_query = cls.get_deleted().select().filter_by(**filters)

            if status == "exists":

                base_query = cls.get_exists().select().filter_by(**filters)

            result = (
                (await db.execute(base_query)).scalars().all()
                if status == "all"
                else (await db.execute(base_query)).all()
            )
            return result # type: ignore
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))

    @classmethod
    def get_order_by(cls, order_by: str) -> Column | None:

        table = Table(cls.__tablename__, MetaData(), autoload_with=engineSync)

        return table.c.get(order_by)

    @classmethod
    async def find_some(
        cls,
        db: AsyncSession,
        pag: int = 1,
        order_by: str = "id",
        ord: str = "asc",
        status: Literal["deleted", "exists", "all"] = "all",
        filters: dict = {},
    ) -> List[Self]:
        try:
            # Determine the source and initial query

            if status == "deleted":

                selectable = cls.get_deleted()

                base_query = selectable.select().filter_by(**filters)

            elif status == "exists":

                selectable = cls.get_exists()

                base_query = selectable.select().filter_by(**filters)

            else:  # status == 'all'

                selectable = cls.__table__ # type: ignore

                base_query = select(cls).filter_by(**filters)

            # Determine the order column

            order_column = None

            if order_by:

                if status == "all":

                    # Try to get from model columns first, then table columns

                    order_column = getattr(cls, order_by, None)

                    if order_column is None:

                        order_column = selectable.c.get(order_by)

                else:

                    order_column = selectable.c.get(order_by)

            # Fallback to id if no order column found

            if order_column is None:

                if status == "all":
                    order_column = cls.id

                else:

                    order_column = selectable.c.get("id")

                    if order_column is None:
                        order_column = cls.id

            # Apply ordering

            if order_column is not None:

                if ord == "desc":

                    base_query = base_query.order_by(order_column.desc())

                else:

                    base_query = base_query.order_by(order_column.asc())

            # Pagination

            if pag <= 0:

                pag = 1

            query = base_query.limit(10).offset((pag - 1) * 10)


            exec_result = await db.execute(query)
            rows = exec_result.scalars().all() if status == "all" else exec_result.all()
            return rows if status == "all" else cls.touple_to_dict(rows) # type: ignore
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))

    @classmethod
    async def find_by_colunm(cls, db: AsyncSession, column: str, value: Any):
        try:
            result = await db.execute(select(cls).where(getattr(cls, column) == value))
            return result
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))

    @classmethod
    async def find_by_specification(cls, db: AsyncSession, specification: dict):
        try:
            result = await db.execute(select(cls).where(**specification))
            return result
        except SQLAlchemyError as e:
            raise DatabaseQueryError(str(e))


class BaseSync(DeclarativeBase):

    uid = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
        primary_key=True,
        default=UUID(),
    )

    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(TIMESTAMP, server_default=func.now())

    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp()
    )

    is_deleted = Column(Boolean, default=False)

    deleted_at = Column(TIMESTAMP, nullable=True)
