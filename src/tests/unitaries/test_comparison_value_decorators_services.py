import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.comparison_values.decorators.services import ComparisonValueDecoratorService
from src.modules.comparison_values.decorators.schemas import RQComparisonValueDecorator
from core.database.models_registry import import_models

# Ensure all models are registered for mapper initialization
import_models()

class TestComparisonValueDecoratorService:
    @pytest.fixture
    def service(self):
        return ComparisonValueDecoratorService()

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_create_decorator(self, service, mock_db):
        # Setup
        data = RQComparisonValueDecorator(
            ref_comparation_values_from=1,
            ref_comparation_values_to=2,
            comparison_decorators={"rate": 1.5}
        )
        
        # Mock DB response for "check if exists"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Execution
        result, error = await service.create_decorator(data, db=mock_db)
        
        # Assertions
        assert error is None
        assert result.ref_comparation_values_from == 1
        assert result.comparison_decorators == {"rate": 1.5}
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_decorator_link_not_found(self, service, mock_db):
        # Mock DB response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Execution
        result, error = await service.get_decorator_link(1, 2, db=mock_db)
        
        # Assertions
        assert result is None
        assert error is not None
        assert "not found" in str(error.message)
