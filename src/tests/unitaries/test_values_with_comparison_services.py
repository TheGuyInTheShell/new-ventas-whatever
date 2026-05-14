import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.services.value_with_comparison import DValueWithComparisonService
from src.domain.schemas.values_with_comparison import (
    RQValueWithComparison,
    QueryValuesWithComparison,
)
from src.modules.values.schemas import RQValue, RSValue
from src.modules.comparison_values.schemas import RQComparisonValue, RSComparisonValue
from src.modules.business_entities.models import BusinessEntity
from src.modules.business_entities.meta.models import MetaBusinessEntity
from src.modules.business_entities_groups.models import BusinessEntitiesGroup
from src.modules.business_entities_groups.connection.models import (
    BusinessEntitiesGroupConnection,
)


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

    async def test_save_value_with_comparison(
        self, values_with_comparison_service, mock_db
    ):
        create_dto = RQValueWithComparison(
            value=RQValue(
                name="Test Comp Val",
                expression="EUR",
                type="currency",
                ref_business_entity=1,
            ),
            comparison_value=RQComparisonValue(
                quantity_from=1, quantity_to=1.2, value_to=2, ref_business_entity=1
            ),
        )

        # Mock sub-services
        mock_saved_value = RSValue(
            id=10,
            uid="val-123",
            name="Test Comp Val",
            expression="EUR",
            type="currency",
            ref_business_entity=1,
            identifier=None,
            meta=[],
            balances=[],
            comparison=None,
        )
        values_with_comparison_service.ValuesService.create_value_with_meta = AsyncMock(
            return_value=(mock_saved_value, None)
        )

        mock_saved_comp = RSComparisonValue(
            id=20,
            uid="comp-123",
            quantity_from=1,
            quantity_to=1.2,
            value_from=10,  # Inherited from saved_value
            value_to=2,
            ref_business_entity=1,
        )
        values_with_comparison_service.ComparisonValuesService.create_comparison = (
            AsyncMock(return_value=(mock_saved_comp, None))
        )

        result, error = (
            await values_with_comparison_service.save_value_with_comparison_service(
                create_dto, db=mock_db
            )
        )

        # Assertions
        assert error is None
        assert result is not None
        assert result.value.id == 10
        assert result.value.ref_business_entity == 1
        assert result.comparison_value.id == 20
        assert result.comparison_value.value_from == 10  # Was automatically linked
        assert result.comparison_value.ref_business_entity == 1

        # DB Commit was called
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_any_call(mock_saved_value)
        mock_db.refresh.assert_any_call(mock_saved_comp)

    async def test_get_values_with_comparison_service(
        self, values_with_comparison_service, mock_db
    ):
        query_dto = QueryValuesWithComparison(ref_business_entity=5)

        mock_result = MagicMock()

        # We need to mock the builder
        with patch(
            "src.domain.services.value_with_comparison.BuilderValueWithComparison"
        ) as MockBuilder:
            mock_builder_instance = MockBuilder.return_value
            mock_builder_instance.set_query.return_value = mock_builder_instance
            mock_builder_instance.build.return_value = mock_builder_instance
            mock_builder_instance.execute = AsyncMock(return_value=mock_result)

            result, error = (
                await values_with_comparison_service.get_values_with_comparison_service(
                    query_dto, db=mock_db
                )
            )

            assert error is None
            assert result == mock_result
            MockBuilder.assert_called_once_with(mock_db)
            mock_builder_instance.set_query.assert_called_once_with(query_dto)
            mock_builder_instance.build.assert_called_once()
            mock_builder_instance.execute.assert_called_once()

    async def test_update_children_recursively_reactive(self, mock_db):
        from src.domain.services.value_with_comparison import (
            _update_children_recursively,
        )

        class MockComp:
            def __init__(self, id, value_from, quantity_to):
                self.id = id
                self.value_from = value_from
                self.quantity_to = quantity_to

        # Data for Comparisons
        mock_comp_10 = MockComp(100, 10, 100.0)  # Parent 1 (Updated)
        mock_comp_11 = MockComp(110, 11, 50.0)  # Parent 2 (Static)
        mock_comp_20 = MockComp(200, 20, 0.0)  # Child 1 (Reactive)
        mock_comp_30 = MockComp(300, 30, 0.0)  # Child 2 (Not Reactive)
        mock_comp_40 = MockComp(400, 40, 0.0)  # Grandchild (Reactive)

        affected_comparisons = []

        def execute_side_effect(stmt):
            stmt_str = str(stmt).lower()
            mock_res = MagicMock()
            params = stmt.compile().params

            def get_all_vals(prefix):
                return [v for k, v in params.items() if k.startswith(prefix)]

            def get_single_val(prefix):
                vals = get_all_vals(prefix)
                return vals[0] if vals else None

            # 1. Hierarchy Queries
            # Distinguish by which parameter is present in the WHERE clause,
            # NOT by what appears in the SELECT clause (both queries SELECT
            # ref_value_top, so string-matching on the SQL text is unreliable).
            if "values_hierarchy" in stmt_str:
                child_val = get_single_val(
                    "ref_value_bottom"
                )  # WHERE ref_value_bottom = ?
                parent_val = get_single_val("ref_value_top")  # WHERE ref_value_top = ?

                if child_val is not None:
                    # SELECT ref_value_top WHERE ref_value_bottom = child_val → get parents
                    if child_val == 20:
                        mock_res.scalars.return_value.all.return_value = [10, 11]
                    elif child_val == 40:
                        mock_res.scalars.return_value.all.return_value = [20]
                    else:
                        mock_res.scalars.return_value.all.return_value = []

                elif parent_val is not None:
                    # SELECT ref_value_bottom WHERE ref_value_top = parent_val → get children
                    if parent_val == 10:
                        mock_res.scalars.return_value.all.return_value = [20, 30]
                    elif parent_val == 20:
                        mock_res.scalars.return_value.all.return_value = [40]
                    else:
                        mock_res.scalars.return_value.all.return_value = []

            # 2. Comparison Value Queries (using 'comparation_values' due to DB naming)
            elif (
                "comparation_values" in stmt_str
                and "meta_comparison_values" not in stmt_str
            ):
                # SQLAlchemy postcompile stores IN-list as a single param value that is a list,
                # e.g. {'value_from_1': [10, 11]} — flatten all value_from params into one list.
                raw_vals = get_all_vals("value_from")
                flat_vals = []
                for v in raw_vals:
                    if isinstance(v, (list, tuple)):
                        flat_vals.extend(v)
                    else:
                        flat_vals.append(v)

                if "postcompile" in str(stmt).lower() or len(flat_vals) > 1:
                    # IN query (SQLAlchemy uses postcompile for .in_())
                    comps = []
                    if 10 in flat_vals:
                        comps.append(mock_comp_10)
                    if 11 in flat_vals:
                        comps.append(mock_comp_11)
                    if 20 in flat_vals:
                        comps.append(mock_comp_20)
                    mock_res.scalars.return_value.all.return_value = comps
                else:
                    # Single fetch
                    val_from = flat_vals[0] if flat_vals else None
                    if val_from == 20:
                        mock_res.scalars.return_value.first.return_value = mock_comp_20
                    elif val_from == 30:
                        mock_res.scalars.return_value.first.return_value = mock_comp_30
                    elif val_from == 40:
                        mock_res.scalars.return_value.first.return_value = mock_comp_40
                    else:
                        mock_res.scalars.return_value.first.return_value = None

            # 3. Meta Comparison Queries (REACTIVE_UPDATE)
            elif "meta_comparison_values" in stmt_str:
                comp_id = get_single_val("ref_comparison_value")
                if comp_id in [200, 400]:  # Child 20 and Grandchild 40 are reactive
                    mock_res.scalars.return_value.first.return_value = MagicMock()
                else:
                    mock_res.scalars.return_value.first.return_value = None

            return mock_res

        mock_db.execute.side_effect = execute_side_effect

        def add_side_effect(obj):
            affected_comparisons.append(obj)

        mock_db.add.side_effect = add_side_effect

        # Act: Update parent 10 and trigger recursive update
        await _update_children_recursively(updated_value_id=10, db=mock_db)

        # Assertions
        assert (
            mock_comp_20 in affected_comparisons
        ), "Reactive child 20 should be updated"
        assert (
            mock_comp_30 not in affected_comparisons
        ), "Non-reactive child 30 should not be updated"
        assert (
            mock_comp_40 in affected_comparisons
        ), "Reactive grandchild 40 should be updated via recursion"

        # Check aggregation for child 20: 100 (parent 10) + 50 (parent 11) = 150
        assert mock_comp_20.quantity_to == 150.0

        # Check propagation to grandchild 40: inherits from parent 20 (which is now 150)
        assert mock_comp_40.quantity_to == 150.0
