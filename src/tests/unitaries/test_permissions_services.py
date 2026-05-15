import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.permissions.services import PermissionsService
from src.modules.permissions.schemas import CreatePermission, BulkPermission
from src.modules.permissions.models import Permission
from src.modules.roles.models import Role
from src.modules.role_permissions.models import RolePermission
from src.modules.options.models import Options
import json
import hashlib

@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    # Configure mock to behave like a session
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db

@pytest.fixture
def permissions_service():
    return PermissionsService()

@pytest.mark.asyncio
class TestPermissionsServiceUnitaries:
    
    async def test_create_permission(self, permissions_service, mock_db):
        create_dto = CreatePermission(
            name="test_perm",
            action="read",
            description="A test permission",
            type="API"
        )
        
        # We need to mock the permission's own save method since it calls BaseModel save
        with patch("src.modules.permissions.models.Permission.save", new_callable=AsyncMock) as mock_save:
            result = await permissions_service.create_permission(mock_db, create_dto)
            
            assert result.name == "test_perm"
            assert result.action == "read"
            assert result.type == "API"
            mock_save.assert_called_once_with(mock_db)

    async def test_generate_permissions_hash(self, permissions_service):
        mock_route_1 = MagicMock()
        mock_route_1.name = "route1"
        mock_route_1.path = "/api/v1/route1"
        mock_route_1.methods = {"GET"}
        
        mock_route_2 = MagicMock()
        mock_route_2.name = "route2"
        mock_route_2.path = "/api/v1/route2"
        mock_route_2.methods = {"POST"}
        
        routes = [mock_route_1, mock_route_2]
        
        hash_result = permissions_service._generate_permissions_hash(routes, "API")
        
        # Verify it generates a valid SHA-256 hex string (64 chars)
        assert len(hash_result) == 64
        
        # Verify deterministic nature
        hash_result_2 = permissions_service._generate_permissions_hash(routes, "API")
        assert hash_result == hash_result_2

    async def test_collect_api_routes(self, permissions_service):
        from fastapi.routing import APIRoute
        from starlette.routing import Mount, Route
        
        api_route_1 = APIRoute("/route1", lambda: None, name="route1")
        non_api_route = Route("/route2", lambda: None, name="route2")
        
        mock_mount = MagicMock(spec=Mount)
        mock_mount.routes = [APIRoute("/route3", lambda: None, name="route3")]
        
        routes = [api_route_1, non_api_route, mock_mount]
        
        collected = permissions_service._collect_api_routes(routes)
        
        assert len(collected) == 2
        assert collected[0].name == "route1"
        assert collected[1].name == "route3"

    async def test_get_permission(self, permissions_service, mock_db):
        mock_result = MagicMock()
        mock_permission = Permission(name="test", action="read", type="API", context="global")
        mock_result.scalar_one_or_none.return_value = mock_permission
        
        mock_db.execute.return_value = mock_result
        
        result = await permissions_service.get_permission(
            name="test", context="global", action="read", type_str="API", db=mock_db
        )
        
        assert result is not None
        assert result.name == "test"
        mock_db.execute.assert_called_once()

    async def test_check_role_has_permission(self, permissions_service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = RolePermission(role_id=1, permission_id=2)
        mock_db.execute.return_value = mock_result
        
        result = await permissions_service.check_role_has_permission(1, 2, db=mock_db)
        
        assert result is True
        mock_db.execute.assert_called_once()

@pytest.mark.asyncio
class TestPermissionsServiceIntegration:
    """
    Since SQLite doesn't support Postgres' composite autoincrement primary keys,
    we test integration flows by mocking the DB session but executing the full
    service methods to verify query building, multiple steps execution, and rollback/commit logic.
    """
    async def test_sync_permission_metadata(self, permissions_service, mock_db):
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute.return_value = mock_result
        
        meta_input = {"key1": "value1", "key2": {"nested": "value"}}
        
        result = await permissions_service._sync_permission_metadata(mock_db, 1, meta_input)
        
        assert result == meta_input
        # Verify db.add was called twice (for key1 and key2)
        assert mock_db.add.call_count == 2
        mock_db.execute.assert_called_once()

    async def test_create_bulk_permissions_with_roles(self, permissions_service, mock_db):
        bulk_data = [
            BulkPermission(
                name="perm_1",
                action="read",
                description="Read perms",
                type="API",
                role_id=1,
                meta={"module": "users"}
            )
        ]
        
        # Mock permission query to return None (so it creates one)
        mock_perm_query = MagicMock()
        mock_perm_query.scalar_one_or_none.return_value = None
        
        # Mock role link query to return None (so it creates link)
        mock_rp_query = MagicMock()
        mock_rp_query.scalar_one_or_none.return_value = None
        
        # Sequentially return queries
        mock_db.execute.side_effect = [mock_perm_query, mock_rp_query, MagicMock()] # 3rd for meta sync
        
        # We also need to mock _sync_permission_metadata to avoid its own DB calls
        with patch.object(permissions_service, "_sync_permission_metadata", new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = {"module": "users"}
            
            # Use PropertyMock to set id and uid
            with patch("src.modules.permissions.models.Permission.id", new_callable=PropertyMock) as mock_id:
                with patch("src.modules.permissions.models.Permission.uid", new_callable=PropertyMock) as mock_uid:
                    mock_id.return_value = 1
                    mock_uid.return_value = "uid-1234"
                    results, success, errors = await permissions_service.create_bulk_permissions_with_roles(mock_db, bulk_data)
                    
                    assert success == 1
                    assert errors == 0
                    assert len(results) == 1
                    assert results[0].success is True
                    assert results[0].permission.name == "perm_1"
                    assert mock_db.add.call_count >= 1 # Should add permission and RolePermission link
                    assert mock_db.commit.call_count >= 1

    async def test_shield_permissions_sync_retry_and_success(self, permissions_service, mock_db):
        registry_dict = {
            "permissions": [
                {
                    "name": "RootNode",
                    "permissions": [
                        {
                            "name": "shield_perm_1",
                            "action": "execute",
                            "description": "Test Shield",
                            "type": "SHIELD",
                            "context": "testing"
                        }
                    ]
                }
            ]
        }
        
        # Mock the queries executed by _process_shield_permissions
        # 1. Option query
        # 2. Existing perms query
        # 3. Role 'owner' query
        # 4. Existing links query
        
        mock_opt = MagicMock()
        mock_opt.scalar_one_or_none.return_value = None # No existing hash
        
        mock_perms = MagicMock()
        mock_perms.scalars().all.return_value = [] # No existing perms
        
        mock_owner = MagicMock()
        mock_owner_role = Role(name="owner", id=1)
        mock_owner.scalar_one_or_none.return_value = mock_owner_role # Owner exists
        
        mock_links = MagicMock()
        mock_links.scalars().all.return_value = [] # No existing links
        
        mock_db.execute.side_effect = [mock_opt, mock_perms, mock_owner, mock_links]
        
        # Avoid flush failing due to missing active transaction in pure mock
        mock_db.flush = AsyncMock()
        
        with patch("src.modules.permissions.models.Permission.id", new_callable=PropertyMock) as mock_id:
            mock_id.return_value = 1
            await permissions_service._process_shield_permissions(registry_dict, lambda: mock_db)
        
        # Verify db logic was traversed correctly
        assert mock_db.commit.call_count == 1
        assert mock_db.close.call_count == 1
        # Added Option, Permission, RolePermission
        assert mock_db.add.call_count > 0 
        assert mock_db.add_all.call_count > 0
