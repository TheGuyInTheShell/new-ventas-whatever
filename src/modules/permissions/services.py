from typing import List, Callable

from fastapi.routing import APIRoute, BaseRoute
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .models import Permission
from .schemas import RQCreatePermission, RQBulkPermission, RSPermission, RSBulkPermissionResult
from app.modules.roles.models import Role
from app.modules.role_permissions.models import RolePermission
from app.modules.permissions.meta.models import MetaPermissions
from app.modules.options.models import Options
from sqlalchemy import select
import hashlib
import json
import functools


async def create_permission(
    db: AsyncSession,
    name: str,
    action: str,
    description: str,
    type: str
) -> Permission:
    """
    Crea un solo permiso en la base de datos.
    
    Args:
        db: Sesión de base de datos
        name: Nombre del permiso
        action: Acción del permiso (GET, POST, PUT, DELETE, etc.)
        description: Descripción del permiso
        type: Tipo del permiso (api, admin, etc.)
        
    Returns:
        Permission: El permiso creado
        
    Raises:
        Exception: Si hay un error al crear el permiso
    """
    permission = Permission(
        name=name,
        action=action,
        description=description,
        type=type,
    )
    await permission.save(db)
    return permission


async def create_bulk_permissions_with_roles(
    db: AsyncSession,
    permissions_data: List[RQBulkPermission]
) -> tuple[List[RSBulkPermissionResult], int, int]:
    """
    Crea múltiples permisos y los asigna a sus roles correspondientes.
    Handles existing permissions gracefully by updating them and ensuring role links.
    """
    from sqlalchemy.exc import IntegrityError # type: ignore
    
    results: List[RSBulkPermissionResult] = []
    success_count = 0
    error_count = 0
    
    for perm_data in permissions_data:
        try:
            # 1. Ensure permission exists (get or create)
            query = await db.execute(select(Permission).where(Permission.name == perm_data.name))
            permission = query.scalar_one_or_none()
            
            if not permission:
                # Create new
                permission = Permission(
                    name=perm_data.name,
                    action=perm_data.action,
                    description=perm_data.description,
                    type=perm_data.type
                )
                db.add(permission)
                try:
                    await db.commit()
                    await db.refresh(permission)
                except IntegrityError:
                    await db.rollback()
                    # Someone else created it or it was concurrent
                    query = await db.execute(select(Permission).where(Permission.name == perm_data.name))
                    permission = query.scalar_one_or_none()
            else:
                # Update existing (optionally update action/description)
                permission.action = perm_data.action
                permission.description = perm_data.description
                permission.type = perm_data.type
                await db.commit()
                await db.refresh(permission)
            
            if not permission:
                raise Exception(f"Permission {perm_data.name} not found")

            permission_id = permission.id
            role_id = perm_data.role_id

            # 2. Link to target role via Pivot Table (RolePermission)
            rp_query = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                )
            )
            if not rp_query.scalar_one_or_none():
                try:
                    db.add(RolePermission(role_id=role_id, permission_id=permission_id))
                    await db.commit()
                except IntegrityError:
                    await db.rollback()
                    # Already linked, ignore

            # 3. Update MetaPermissions (EAV)
            current_meta = {}
            if perm_data.meta and isinstance(perm_data.meta, dict):
                # Fetch existing meta
                meta_query = await db.execute(
                    select(MetaPermissions).where(MetaPermissions.ref_permission == permission_id)
                )
                existing_metas = {m.key: m for m in meta_query.scalars().all()}

                for key, value in perm_data.meta.items():
                    str_value = str(value)
                    if key in existing_metas:
                        if existing_metas[key].value != str_value:
                            existing_metas[key].value = str_value
                            await db.commit()
                    else:
                        new_meta = MetaPermissions(
                            key=key,
                            value=str_value,
                            ref_permission=permission_id
                        )
                        db.add(new_meta)
                        await db.commit()
                    current_meta[key] = value

            # 4. Sync the Role's permissions array (redundancy)
            role = await Role.find_one(db, role_id)
            if role:
                current_perms = set(role.permissions or [])
                if permission_id not in current_perms:
                    current_perms.add(permission_id)
                    await role.update(db, role_id, {"permissions": list(current_perms)})

            # Success
            results.append(RSBulkPermissionResult(
                permission=RSPermission(
                    id=permission.id,
                    uid=permission.uid,
                    type=permission.type,
                    name=permission.name,
                    action=permission.action,
                    description=permission.description,
                    meta=current_meta,
                ),
                role_id=role_id,
                success=True,
                error=None
            ))
            success_count += 1
            
        except Exception as e:
            print(f"[Bulk Seeding] Error processing {perm_data.name}: {e}")
            await db.rollback()
            results.append(RSBulkPermissionResult(
                permission=RSPermission(
                    id=0, uid="", type=perm_data.type, name=perm_data.name,
                    action=perm_data.action, description=perm_data.description, meta=perm_data.meta
                ),
                role_id=perm_data.role_id,
                success=False,
                error=str(e)
            ))
            error_count += 1
    
    return results, success_count, error_count
def collect_api_routes(routes: List[BaseRoute]) -> List[APIRoute]:
    """Recursively collect all APIRoute instances including from nested routers."""
    from starlette.routing import Mount # type: ignore
    collected = []
    for route in routes:
        if isinstance(route, APIRoute):
            collected.append(route)
        elif isinstance(route, Mount) and hasattr(route, 'routes'):
            collected.extend(collect_api_routes(route.routes))
    return collected


def generate_permissions_hash(routes: List[APIRoute], type_name: str) -> str:
    """
    Generates a unique SHA256 hash based on the route attributes and permission type.
    
    Args:
        routes: List of APIRoute instances
        type_name: The type of permission (e.g., 'api', 'admin')
        
    Returns:
        str: The calculated hash
    """
    route_data = []
    # Sort routes by name to ensure consistent hash
    sorted_routes = sorted(routes, key=lambda r: r.name)
    
    for route in sorted_routes:
        route_data.append({
            "name": route.name,
            "path": route.path,
            "methods": sorted(list(route.methods or []))
        })
    
    hash_payload = {
        "type": type_name,
        "routes": route_data
    }
    
    hash_string = json.dumps(hash_payload, sort_keys=True)
    return hashlib.sha256(hash_string.encode()).hexdigest()


def with_permission_hash_guard(func: Callable):
    """
    Decorator that checks if the permission routes have changed before executing
     the initialization logic.
    """
    @functools.wraps(func)
    async def wrapper(routes: List[BaseRoute], sessionAsync: async_sessionmaker[AsyncSession], type: str, *args, **kwargs):
        db: AsyncSession = sessionAsync()
        try:
            api_routes = collect_api_routes(routes)
            if not api_routes:
                return await func(routes, sessionAsync, type, *args, **kwargs)

            # Generate current hash
            current_hash = generate_permissions_hash(api_routes, type)
            context_name = "system_init"
            option_name = f"permissions_hash_{type}"

            # Check for existing hash in database
            query = await db.execute(
                select(Options).where(
                    Options.context == context_name,
                    Options.name == option_name
                )
            )
            option_record = query.scalar_one_or_none()

            if option_record and option_record.value == current_hash:
                print(f"[Permissions] No changes detected for '{type}' permissions (Hash: {current_hash[:8]}...). Skipping sync.") # type: ignore
                return

            # If hash is different or missing, proceed with the original function
            print(f"[Permissions] Changes detected or initial run for '{type}'. Syncing permissions...")
            result = await func(routes, sessionAsync, type, *args, **kwargs)

            # Update or create the hash record after successful execution
            if option_record:
                option_record.value = current_hash
            else:
                new_option = Options(
                    context=context_name,
                    name=option_name,
                    value=current_hash
                )
                db.add(new_option)
            
            await db.commit()
            print(f"[Permissions] Updated hash for '{type}' permissions.")
            return result

        except Exception as e:
            print(f"[Permissions] Error in hash guard for '{type}': {e}")
            # Fallback: execute original function if something goes wrong with hashing
            return await func(routes, sessionAsync, type, *args, **kwargs)
        finally:
            await db.close()

    return wrapper


async def create_permissions_api(
    routes: List[BaseRoute], sessionAsync: async_sessionmaker[AsyncSession], type: str
):
    db: AsyncSession = sessionAsync()
    try:
        api_routes = collect_api_routes(routes)
        print(f"[Permissions] Found {len(api_routes)} API routes of type '{type}'")

        if not api_routes:
            print(f"[Permissions] No APIRoute instances found for type '{type}', skipping.")
            return

        # 1. Collect unique routes and their details
        route_map = {}
        for route in api_routes:
            if route.name not in route_map:
                route_map[route.name] = route
        
        route_names = list(route_map.keys())

        # 2. Bulk fetch existing permissions for these routes
        existing_perms_query = await db.execute(
            select(Permission).where(Permission.name.in_(route_names))
        )
        existing_perms = {p.name: p for p in existing_perms_query.scalars().all()}

        # 3. Create missing permissions in bulk
        new_permissions = []
        for name, route in route_map.items():
            if name not in existing_perms:
                # Create new permission
                methods: set = route.methods
                new_perm = Permission(
                    name=name,
                    action=next(iter(methods)) if methods else "UNKNOWN",
                    description=route.path,
                    type=type,
                )
                db.add(new_perm)
                new_permissions.append(new_perm)
        
        if new_permissions:
            print(f"[Permissions] Creating {len(new_permissions)} new permissions...")
            await db.flush() # Flush to get IDs for new permissions
            # Merge new permissions into the existing_perms map for role linking
            for p in new_permissions:
                existing_perms[p.name] = p

        # 4. Bulk handle owner role synchronization
        owner_query = await db.execute(select(Role).where(Role.name == "owner"))
        owner_role = owner_query.scalar_one_or_none()
        
        if owner_role:
            # All permission IDs involved in this sync (existing or new)
            all_permission_ids = [p.id for p in existing_perms.values()]
            
            # Bulk fetch existing RolePermission links for the owner role
            existing_links_query = await db.execute(
                select(RolePermission.permission_id).where(
                    RolePermission.role_id == owner_role.id,
                    RolePermission.permission_id.in_(all_permission_ids)
                )
            )
            existing_link_ids = set(existing_links_query.scalars().all())

            # Identify links that need to be created
            new_links = []
            for p_id in all_permission_ids:
                if p_id not in existing_link_ids:
                    new_links.append(RolePermission(role_id=owner_role.id, permission_id=p_id))
            
            if new_links:
                print(f"[Permissions] Linking {len(new_links)} new permissions to owner role...")
                db.add_all(new_links)
        
        # 5. Commit all changes once
        await db.commit()
        print(f"[Permissions] Bulk sync completed successfully for '{type}'.")

    except Exception as e:
        print(f"[Permissions] Critical error in create_permissions_api: {e}")
        import traceback
        traceback.print_exc()
        await db.rollback()
    finally:
        await db.close()
