import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.comparison_values.services import ComparisonValuesService
from src.modules.comparison_values.schemas import RQComparisonValue, RQMetaComparisonValue
from src.modules.comparison_values.models import ComparisonValue
from src.modules.comparison_values.meta.models import MetaComparisonValue
from src.modules.comparison_values.historical.models import ComparisonValueHistorical
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
def comparison_values_service():
    return ComparisonValuesService()

@pytest.mark.asyncio
class TestComparisonValuesServiceUnitaries:
    
    async def test_create_comparison(self, comparison_values_service, mock_db):
        meta_data = [RQMetaComparisonValue(key="test_key", value="test_value")]
        create_dto = RQComparisonValue(
            quantity_from=1,
            quantity_to=10.5,
            value_from=1,
            value_to=2,
            ref_business_entity=100,
            meta=meta_data
        )
        
        # Mock DB execute for selectinload refresh
        mock_result = MagicMock()
        mock_comparison = MagicMock()
        mock_comparison.id = 1
        mock_comparison.ref_business_entity = 100
        mock_result.scalar_one.return_value = mock_comparison
        mock_db.execute.return_value = mock_result
        
        # Mock the comparison save method since it's a BasicBaseAsync model
        with patch("src.modules.comparison_values.models.ComparisonValue.save", new_callable=AsyncMock) as mock_save:
            with patch("src.modules.comparison_values.meta.models.MetaComparisonValue.save", new_callable=AsyncMock) as mock_meta_save:
                result, error = await comparison_values_service.create_comparison(create_dto, db=mock_db)
                
                assert error is None
                assert result.id == 1
                assert result.ref_business_entity == 100
                
                mock_save.assert_called_once_with(mock_db)
                mock_meta_save.assert_called_once_with(mock_db)
                mock_db.execute.assert_called_once()

    @patch("src.modules.comparison_values.models.ComparisonValue.update", new_callable=AsyncMock)
    @patch("src.modules.comparison_values.models.ComparisonValue.find_one", new_callable=AsyncMock)
    async def test_update_comparison_triggers_historical(self, mock_find_one, mock_update, comparison_values_service, mock_db):
        update_dto = RQComparisonValue(
            quantity_from=1,
            quantity_to=20.0, # changed from 10.5
            value_from=1,
            value_to=2,
            ref_business_entity=100
        )
        
        mock_existing = MagicMock()
        mock_existing.id = 1
        mock_existing.quantity_to = 10.5 # old price
        mock_existing.ref_business_entity = 100
        mock_find_one.return_value = mock_existing
        
        # Mock DB execute for the refresh query
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_existing
        mock_db.execute.return_value = mock_result
        
        with patch.object(comparison_values_service, "create_historical_snapshot", new_callable=AsyncMock) as mock_snapshot:
            mock_snapshot.return_value = (MagicMock(), None)
            result, error = await comparison_values_service.update_comparison(1, update_dto, db=mock_db)
            assert error is None
            
            # Verify historical snapshot was created because price changed
            mock_snapshot.assert_called_once_with(mock_existing)
            mock_update.assert_called_once()

    async def test_find_comparison_rate_direct(self, comparison_values_service, mock_db):
        mock_result = MagicMock()
        mock_comp = MagicMock()
        mock_comp.quantity_from = 1
        mock_comp.quantity_to = 50.0
        mock_result.scalar_one_or_none.return_value = mock_comp
        mock_db.execute.return_value = mock_result
        
        result, error = await comparison_values_service.find_comparison_rate(1, 2, db=mock_db)
        
        assert error is None
        assert result is not None
        rate, is_direct = result
        assert rate == 50.0
        assert is_direct is True
        
        # db.execute called once because it found direct match
        mock_db.execute.assert_called_once()

    async def test_find_comparison_rate_inverse(self, comparison_values_service, mock_db):
        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None
        
        mock_result_found = MagicMock()
        mock_comp = MagicMock()
        mock_comp.quantity_from = 1
        mock_comp.quantity_to = 50.0
        mock_result_found.scalar_one_or_none.return_value = mock_comp
        
        # First call returns None (direct not found), second returns comp (inverse found)
        mock_db.execute.side_effect = [mock_result_none, mock_result_found]
        
        result, error = await comparison_values_service.find_comparison_rate(2, 1, db=mock_db)
        
        assert error is None
        assert result is not None
        rate, is_direct = result
        assert rate == 1.0 / 50.0
        assert is_direct is False
        
        assert mock_db.execute.call_count == 2

    @patch("src.modules.values.models.Value.find_one", new_callable=AsyncMock)
    async def test_convert_value(self, mock_find_value, comparison_values_service, mock_db):
        mock_from_value = MagicMock()
        mock_to_value = MagicMock()
        mock_find_value.side_effect = [mock_from_value, mock_to_value]
        
        with patch.object(comparison_values_service, "find_comparison_rate", new_callable=AsyncMock) as mock_rate:
            mock_rate.return_value = ((50.0, True), None) # 1 USD = 50 VES
            
            result, error = await comparison_values_service.convert_value(1, 2, 10.0, db=mock_db)
            
            assert error is None
            assert result is not None
            assert result["original_amount"] == 10.0
            assert result["converted_amount"] == 500.0
            assert result["rate"] == 50.0
