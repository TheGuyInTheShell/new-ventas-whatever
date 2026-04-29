import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.business_entities.services import BusinessEntitiesService
from src.modules.business_entities.schemas import RQBusinessEntity
from src.modules.business_entities.models import BusinessEntity
from src.modules.business_entities.meta.models import MetaBusinessEntity
from src.modules.business_entities_groups.models import BusinessEntitiesGroup
from src.modules.business_entities_groups.connection.models import BusinessEntitiesGroupConnection

@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db

@pytest.fixture
def business_entities_service():
    return BusinessEntitiesService()

@pytest.mark.asyncio
class TestBusinessEntitiesServiceUnitaries:
    
    async def test_create_business_entity(self, business_entities_service, mock_db):
        create_dto = RQBusinessEntity(
            name="Test Business"
        )
        
        # We need to mock the entity's own save method since it calls BaseModel save
        with patch("src.modules.business_entities.models.BusinessEntity.save", new_callable=AsyncMock) as mock_save:
            result = await business_entities_service.create_business_entity(create_dto, db=mock_db)
            
            assert result.name == "Test Business"
            # Verify the obsolete fields are not present/set (they shouldn't be in the DTO or model)
            assert not hasattr(result, 'context')
            assert not hasattr(result, 'type')
            assert not hasattr(result, 'metadata_info')
            
            mock_save.assert_called_once_with(mock_db)
