from fastapi import Request
from core.lib.register import Controller
from core.lib.decorators import Post, Services
from core.security.shield import Shield

from src.modules.d.services.business_entities_search_by import (
    BusinessEntitiesSearchByService,
)
from src.modules.d.schemas.business_entities_search_by import (
    RQBusinessEntitiesSearch,
    RQBusinessEntitySearch,
    RQBusinessEntitySearchChild,
    RQBusinessEntitySearchGroups,
)


@Shield.register(context="business_entities_search_by")
@Services(BusinessEntitiesSearchByService)
class BusinessEntitiesSearchByController(Controller):

    BusinessEntitiesSearchByService: BusinessEntitiesSearchByService

    @Post("/search", summary="Búsqueda de entidades de negocio por nombre")
    @Shield.need(
        name="search_by_name",
        action="read",
        type="endpoint",
        description="Búsqueda de entidades por nombre con opción de jerarquía y grupos",
    )
    async def search_by_name(self, query: RQBusinessEntitySearch):
        """
        Busca una entidad por su nombre exacto. Permite obtener opcionalmente
        la jerarquía completa y/o los grupos asociados.
        """
        result, error = await self.BusinessEntitiesSearchByService.search_entity_by_name(
            query
        )

        if error:
            return error.to_response()

        return result

    @Post("/search/groups", summary="Búsqueda de entidades de negocio por grupos")
    @Shield.need(
        name="search_by_groups",
        action="read",
        type="endpoint",
        description="Búsqueda de entidades por pertenencia a grupos",
    )
    async def search_by_groups(self, query: RQBusinessEntitySearchGroups):
        """
        Busca entidades que pertenecen a uno o más grupos especificados.
        """
        result, error = await self.BusinessEntitiesSearchByService.search_entity_by_groups(
            query
        )

        if error:
            return error.to_response()

        return result

    @Post("/search/child", summary="Búsqueda de entidades de negocio por padre e hijo")
    @Shield.need(
        name="search_by_child",
        action="read",
        type="endpoint",
        description="Búsqueda de entidades por asociación padre e hijo",
    )
    async def search_by_child(self, query: RQBusinessEntitySearchChild):
        """
        Busca una entidad por su nombre y una asociación específica con un hijo por su nombre.
        La respuesta incluirá los datos de ambos.
        """
        result, error = await self.BusinessEntitiesSearchByService.search_entity_by_child(
            query
        )

        if error:
            return error.to_response()

        return result

    @Post("/search_by", summary="Búsqueda avanzada genérica de entidades de negocio")
    @Shield.need(
        name="search_by",
        action="read",
        type="endpoint",
        description="Búsqueda avanzada genérica de entidades",
    )
    async def search_by(self, query: RQBusinessEntitiesSearch):
        """
        Endpoint genérico para realizar búsquedas avanzadas sobre entidades de negocio,
        permitiendo filtrar por nombre, grupos y relaciones jerárquicas.
        """
        result, error = await self.BusinessEntitiesSearchByService.search_business_entities(
            query
        )

        if error:
            return error.to_response()

        return result
