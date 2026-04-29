import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.d.services.value_with_comparison import DValueWithComparisonService
from src.modules.d.schemas.values_with_comparison import (
    RQValueWithComparison, QueryValuesWithComparison
)
from src.modules.values.schemas import RQValue
from src.modules.comparison_values.schemas import RQComparisonValue
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
    db.execute = AsyncMock()
    return db

@pytest.fixture
def values_with_comparison_service():
    service = DValueWithComparisonService()
    # Mock the injected dependencies
    service.ValuesService = MagicMock()
    service.ComparisonValuesService = MagicMock()
    return service

@pytest.mark.asyncio
class TestValuesWithComparisonServiceUnitaries:
    
    async def test_save_value_with_comparison(self, values_with_comparison_service, mock_db):
        create_dto = RQValueWithComparison(
            value=RQValue(
                name="Test Comp Val",
                expression="EUR",
                type="currency",
                ref_business_entity=1,
            ),
            comparison_value=RQComparisonValue(
                quantity_from=1,
                quantity_to=1.2,
                value_to=2,
                ref_business_entity=1
            )
        )
        
        # Mock sub-services
        mock_saved_value = MagicMock()
        mock_saved_value.id = 10
        mock_saved_value.uid = "val-123"
        mock_saved_value.name = "Test Comp Val"
        mock_saved_value.expression = "EUR"
        mock_saved_value.type = "currency"
        mock_saved_value.ref_business_entity = 1
        mock_saved_value.identifier = None
        values_with_comparison_service.ValuesService.create_value_with_meta = AsyncMock(return_value=mock_saved_value)
        
        mock_saved_comp = MagicMock()
        mock_saved_comp.id = 20
        mock_saved_comp.uid = "comp-123"
        mock_saved_comp.quantity_from = 1
        mock_saved_comp.quantity_to = 1.2
        mock_saved_comp.value_from = 10 # Inherited from saved_value
        mock_saved_comp.value_to = 2
        mock_saved_comp.ref_business_entity = 1
        values_with_comparison_service.ComparisonValuesService.create_comparison = AsyncMock(return_value=mock_saved_comp)
        
        result = await values_with_comparison_service.save_value_with_comparison_service(create_dto, db=mock_db)
        
        # Assertions
        assert result is not None
        assert result.value.id == 10
        assert result.value.ref_business_entity == 1
        assert result.comparison_value.id == 20
        assert result.comparison_value.value_from == 10 # Was automatically linked
        assert result.comparison_value.ref_business_entity == 1
        
        # DB Commit was called
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_any_call(mock_saved_value)
        mock_db.refresh.assert_any_call(mock_saved_comp)

    async def test_get_values_with_comparison_service(self, values_with_comparison_service, mock_db):
        query_dto = QueryValuesWithComparison(
            ref_business_entity=5
        )
        
        mock_result = MagicMock()
        
        # We need to mock the builder
        with patch("src.modules.d.services.value_with_comparison.BuilderValueWithComparison") as MockBuilder:
            mock_builder_instance = MockBuilder.return_value
            mock_builder_instance.set_query.return_value = mock_builder_instance
            mock_builder_instance.build.return_value = mock_builder_instance
            mock_builder_instance.execute = AsyncMock(return_value=mock_result)
            
            result = await values_with_comparison_service.get_values_with_comparison_service(query_dto, db=mock_db)
            
            assert result == mock_result
            MockBuilder.assert_called_once_with(mock_db)
            mock_builder_instance.set_query.assert_called_once_with(query_dto)
            mock_builder_instance.build.assert_called_once()
            mock_builder_instance.execute.assert_called_once()
