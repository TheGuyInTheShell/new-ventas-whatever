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
        values_with_comparison_service.ValuesService.create_value_with_meta = AsyncMock(return_value=(mock_saved_value, None))
        
        mock_saved_comp = MagicMock()
        mock_saved_comp.id = 20
        mock_saved_comp.uid = "comp-123"
        mock_saved_comp.quantity_from = 1
        mock_saved_comp.quantity_to = 1.2
        mock_saved_comp.value_from = 10 # Inherited from saved_value
        mock_saved_comp.value_to = 2
        mock_saved_comp.ref_business_entity = 1
        values_with_comparison_service.ComparisonValuesService.create_comparison = AsyncMock(return_value=(mock_saved_comp, None))
        
        result, error = await values_with_comparison_service.save_value_with_comparison_service(create_dto, db=mock_db)
        
        # Assertions
        assert error is None
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
            
            result, error = await values_with_comparison_service.get_values_with_comparison_service(query_dto, db=mock_db)
            
            assert error is None
            assert result == mock_result
            MockBuilder.assert_called_once_with(mock_db)
            mock_builder_instance.set_query.assert_called_once_with(query_dto)
            mock_builder_instance.build.assert_called_once()
            mock_builder_instance.execute.assert_called_once()

    async def test_update_parents_recursively_lock_and_unlock(self, mock_db):
        from src.modules.d.services.value_with_comparison import _update_parents_recursively
        from src.modules.comparison_values.schemas import RSComparisonValue

        # Mocks
        mock_comp_20 = MagicMock()
        mock_comp_20.id = 200
        mock_comp_20.value_from = 20
        mock_comp_20.quantity_to = 0

        mock_comp_30 = MagicMock()
        mock_comp_30.id = 300
        mock_comp_30.value_from = 30
        mock_comp_30.quantity_to = 0

        mock_comp_40 = MagicMock()
        mock_comp_40.id = 400
        mock_comp_40.value_from = 40
        mock_comp_40.quantity_to = 0

        affected_comparisons = []

        def execute_side_effect(stmt):
            stmt_str = str(stmt).lower()
            mock_res = MagicMock()
            
            # Using basic string matching since we know the order of queries
            # or checking params
            params = stmt.compile().params
            
            if "values_hierarchy" in stmt_str:
                child_val = list(params.values())[0] if params else None
                if child_val == 10:
                    mock_res.scalars.return_value.all.return_value = [20, 30]
                elif child_val == 30:
                    mock_res.scalars.return_value.all.return_value = [40]
                else:
                    mock_res.scalars.return_value.all.return_value = []
                    
            elif "comparation_values" in stmt_str and "meta_comparison_values" not in stmt_str:
                parent_val = list(params.values())[0] if params else None
                if parent_val == 20:
                    mock_res.scalars.return_value.first.return_value = mock_comp_20
                elif parent_val == 30:
                    mock_res.scalars.return_value.first.return_value = mock_comp_30
                elif parent_val == 40:
                    mock_res.scalars.return_value.first.return_value = mock_comp_40
                else:
                    mock_res.scalars.return_value.first.return_value = None
                    
            elif "meta_comparison_values" in stmt_str:
                # Find the comparison ID in the params
                comp_val = None
                for k, v in params.items():
                    if isinstance(v, int):
                        comp_val = v
                
                if comp_val == 200: # Parent 20's comparison ID
                    mock_res.scalars.return_value.first.return_value = True # Is locked
                else:
                    mock_res.scalars.return_value.first.return_value = None # Not locked
                    
            return mock_res
            
        mock_db.execute.side_effect = execute_side_effect
        
        def add_side_effect(obj):
            affected_comparisons.append(obj)
            print(f"Affected comparison updated: value_from={obj.value_from}, new_quantity_to={obj.quantity_to}")
            
        mock_db.add.side_effect = add_side_effect
        
        comparison_data = RSComparisonValue(
            id=99,
            uid="child-comp",
            quantity_from=1,
            quantity_to=5.5,
            value_from=10,
            value_to=2,
            ref_business_entity=1
        )
        
        await _update_parents_recursively(child_id=10, comparison_data=comparison_data, db=mock_db)
        
        # Assertions
        assert mock_comp_20 not in affected_comparisons, "Locked comparison should not be updated"
        assert mock_comp_30 in affected_comparisons, "Unlocked comparison should be updated"
        assert mock_comp_40 in affected_comparisons, "Unlocked child's parent should be updated"
        
        assert mock_comp_30.quantity_to == 5.5
        assert mock_comp_40.quantity_to == 5.5
        
        print("\n--- Final Results ---")
        print(f"Total affected comparisons: {len(affected_comparisons)}")
        for comp in affected_comparisons:
            print(f"- Comparison for parent Value ID {comp.value_from} updated to {comp.quantity_to}")
