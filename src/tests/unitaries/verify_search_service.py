import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.modules.business_entities.models import BusinessEntity
from src.modules.business_entities.meta.models import MetaBusinessEntity
from src.modules.business_entities_groups.models import BusinessEntitiesGroup
from src.modules.business_entities_groups.connection.models import BusinessEntitiesGroupConnection
from src.modules.business_entities.hierarchy.models import BusinessEntitiesHierarchy

from src.modules.d.services.business_entities_search_by import BusinessEntitiesSearchByService
from src.modules.d.schemas.business_entities_search_by import RQBusinessEntitiesSearch

DATABASE_URL = "postgresql+asyncpg://postgres:Mf9vEKl7tXbGcdKb3XtlstDBPKFcDW6ljGHjnP2tm4R4CMFGdGbGJ7Bv55Th1rgo@185.194.140.61:5432/postgres"

async def verify_search_service():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        service = BusinessEntitiesSearchByService()
        
        print("--- Verificando Busqueda por Nombre ('chinese') ---")
        query = RQBusinessEntitiesSearch(name="chinese")
        result, error = await service.search_business_entities(query, db=db)
        
        if error:
            print(f"ERROR en busqueda por nombre: {error.message} (Code: {error.code})")
        else:
            print(f"SUCCESS: Total: {result.total}")
            for item in result.data:
                print(f" - {item.name} (Groups: {item.groups})")

        print("\n--- Verificando Busqueda por Parent ID (hijos de 'chinese-restaurant') ---")
        # Primero buscamos el ID
        q_parent = RQBusinessEntitiesSearch(name="chinese-restaurant")
        res_parent, err_parent = await service.search_business_entities(q_parent, db=db)
        
        if err_parent:
            print(f"ERROR buscando padre: {err_parent.message}")
        elif res_parent and res_parent.data:
            parent_id = res_parent.data[0].id
            print(f"SUCCESS: Parent ID found: {parent_id}")
            
            query_h = RQBusinessEntitiesSearch(parent_id=parent_id)
            result_h, err_h = await service.search_business_entities(query_h, db=db)
            
            if err_h:
                print(f"ERROR buscando hijos: {err_h.message}")
            else:
                print(f"SUCCESS: Hijos encontrados: {result_h.total}")
                for item in result_h.data:
                    print(f" - {item.name}")
        else:
            print("WARNING: No se encontro la entidad 'chinese-restaurant'")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_search_service())
