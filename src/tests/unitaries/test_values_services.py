import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.values.services import ValuesService
from src.modules.values.schemas import RQValue, RQMetaValue, RQValueQuery
from src.modules.values.models import Value
from src.modules.values.meta.models import MetaValue
from src.modules.comparison_values.models import ComparisonValue
from src.modules.comparison_values.meta.models import MetaComparisonValue
from src.modules.balances.models import Balance
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
def values_service():
    return ValuesService()

@pytest.mark.asyncio
class TestValuesServiceUnitaries:
    
    async def test_create_value_with_meta(self, values_service, mock_db):
        meta_data = [RQMetaValue(key="test_key", value="test_value")]
        create_dto = RQValue(
            name="Test Value",
            expression="USD",
            type="currency",
            ref_business_entity=1,
            identifier="test-123",
            meta=meta_data,
            price=None,
            currency_id=None
        )
        
        # Mock the db.execute for the selectinload refresh
        mock_result = MagicMock()
        mock_value = MagicMock()
        mock_value.id = 1
        mock_value.uid = "test-uid-1"
        mock_value.name = "Test Value"
        mock_value.expression = "USD"
        mock_value.type = "currency"
        mock_value.ref_business_entity = 1
        mock_value.identifier = "test-123"
        mock_value.comparison = None
        mock_value.balances = []
        mock_value.meta = []
        mock_result.scalar_one_or_none.return_value = mock_value
        mock_db.execute.return_value = mock_result
        
        result, error = await values_service.create_value_with_meta(create_dto, db=mock_db)
        
        assert error is None
        assert result.name == "Test Value"
        assert result.ref_business_entity == 1
        
        # We expect db.add to be called twice: once for Value, once for MetaValue
        assert mock_db.add.call_count == 2
        assert mock_db.flush.call_count == 2
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    async def test_create_value_with_price_comparison(self, values_service, mock_db):
        create_dto = RQValue(
            name="Test Item",
            expression="ITEM",
            type="inventory",
            ref_business_entity=2,
            price=10.5,
            currency_id=1
        )
        
        mock_result = MagicMock()
        mock_value = MagicMock()
        mock_value.id = 5
        mock_value.uid = "test-uid-5"
        mock_value.name = "Test Item"
        mock_value.expression = "ITEM"
        mock_value.type = "inventory"
        mock_value.ref_business_entity = 2
        mock_value.identifier = None
        mock_value.comparison = None
        mock_value.balances = []
        mock_value.meta = []
        mock_result.scalar_one_or_none.return_value = mock_value
        mock_db.execute.return_value = mock_result
        
        result, error = await values_service.create_value_with_meta(create_dto, db=mock_db)
        assert error is None
        
        # Called add twice: once for Value, once for ComparisonValue (no meta)
        assert mock_db.add.call_count == 2
        
        # Get the arguments passed to db.add
        add_calls = mock_db.add.call_args_list
        # Second call should be ComparisonValue
        comparison_obj = add_calls[1][0][0]
        
        from src.modules.comparison_values.models import ComparisonValue
        assert isinstance(comparison_obj, ComparisonValue)
        assert comparison_obj.quantity_to == 10.5
        assert comparison_obj.value_to == 1
        assert comparison_obj.ref_business_entity == 2 # Assuming it takes it from Value or sets it? Wait!

    @patch("src.modules.values.models.Value.update", new_callable=AsyncMock)
    @patch("src.modules.values.models.Value.find_one", new_callable=AsyncMock)
    @patch("src.modules.values.meta.models.MetaValue.find_all", new_callable=AsyncMock)
    @patch("src.modules.values.meta.models.MetaValue.delete_by_specification", new_callable=AsyncMock)
    @patch("src.modules.values.meta.models.MetaValue.save", new_callable=AsyncMock)
    async def test_update_value_with_meta(self, mock_meta_save, mock_meta_delete, mock_meta_find_all, mock_value_find_one, mock_value_update, values_service, mock_db):
        update_dto = RQValue(
            name="Updated Value",
            expression="UPD",
            type="currency",
            ref_business_entity=1,
            meta=[RQMetaValue(key="new_key", value="new_val")]
        )
        
        mock_value = MagicMock()
        mock_value.id = 1
        mock_value.name = "Updated Value"
        mock_value.uid = "test-uid"
        mock_value.expression = "UPD"
        mock_value.type = "currency"
        mock_value.ref_business_entity = 1
        mock_value.identifier = None
        mock_value.comparison = None
        mock_value.meta = []
        mock_value.balances = []
        mock_value_update.return_value = mock_value
        mock_value_find_one.return_value = mock_value
        
        mock_existing_meta = MagicMock()
        mock_existing_meta.id = 10
        mock_meta_find_all.return_value = [mock_existing_meta]
        
        result, error = await values_service.update_value_with_meta(1, update_dto, db=mock_db)
        
        assert error is None
        
        mock_value_update.assert_called_once()
        # delete_by_specification is called with the ref_value spec — find_all is no longer used
        mock_meta_delete.assert_called_once_with(mock_db, specification={"ref_value": mock_value.id})
        mock_meta_save.assert_called_once()
        
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_value)

    @patch("src.modules.values.models.Value.query", new_callable=AsyncMock)
    async def test_get_values_paginated(self, mock_query, values_service, mock_db):
        m1 = MagicMock()
        m1.id = 1; m1.uid = "uid1"; m1.name = "n1"; m1.expression = "e1"; m1.type = "t1"; m1.ref_business_entity = 1; m1.identifier = "i1"; m1.meta = []; m1.balances = []; m1.comparison = None
        m2 = MagicMock()
        m2.id = 2; m2.uid = "uid2"; m2.name = "n2"; m2.expression = "e2"; m2.type = "t2"; m2.ref_business_entity = 1; m2.identifier = "i2"; m2.meta = []; m2.balances = []; m2.comparison = None
        
        mock_query.return_value = ([m1, m2], 3)
        
        query = RQValueQuery(page=1, page_size=2)
        result, error = await values_service.get_values_paginated(query, db=mock_db)
        
        assert error is None
        assert len(result.data) == 2
        assert result.total == 3
        mock_query.assert_called_once()
