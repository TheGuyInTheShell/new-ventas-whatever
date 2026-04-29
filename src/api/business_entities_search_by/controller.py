from fastapi import Request
from core.lib.register import Controller
from core.lib.decorators import Post, Services
from core.security.shield import Shield

from src.modules.d.services.business_entities_search_by import BusinessEntitiesSearchByService
from src.modules.d.schemas.business_entities_search_by import RQBusinessEntitiesSearch


@Services(BusinessEntitiesSearchByService)
class BusinessEntitiesSearchByController(Controller):
    
    BusinessEntitiesSearchByService: BusinessEntitiesSearchByService
    
    @Post("/search", summary="Búsqueda compleja de entidades de negocio")
    @Shield.need(name="business_entities:search", action="read", type="endpoint", description="Búsqueda avanzada de entidades")
    async def search(self, query: RQBusinessEntitiesSearch):
        """
        Endpoint para realizar búsquedas avanzadas sobre entidades de negocio,
        permitiendo filtrar por nombre, grupos y relaciones jerárquicas.
        """
        result, error = await self.BusinessEntitiesSearchByService.search_business_entities(query)
        
        if error:
            return error.to_response()
            
        return result
