from fastapi import Depends
from typing import List, Callable, Any, Dict
from fastapi.routing import APIRoute, BaseRoute
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError
import hashlib
import json
import functools
import traceback

from core.lib.register.service import Service
from core.database import get_async_db
from fastapi_injectable import injectable
from .models import Permission
from .schemas import RQCreatePermission, RQBulkPermission, RSPermission, RSBulkPermissionResult
from ..roles.models import Role
from ..role_permissions.models import RolePermission
from .meta.models import MetaPermissions
from ..options.models import Options

def with_permission_hash_guard(func: Callable):
    """
    Decorator that checks if the permission routes have changed before executing
     the initialization logic.
    Assumes the decorated function is a method of PermissionsService.
    """
    @functools.wraps(func)
    async def wrapper(self, routes: List[BaseRoute], sessionAsync: async_sessionmaker[AsyncSession], type: str, *args, **kwargs):
        db: AsyncSession = sessionAsync()
        try:
            api_routes = self._collect_api_routes(routes)
            if not api_routes:
                return await func(self, routes, sessionAsync, type, *args, **kwargs)

            # Generate current hash
            current_hash = self._generate_permissions_hash(api_routes, type)
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
            result = await func(self, routes, sessionAsync, type, *args, **kwargs)

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
            return await func(self, routes, sessionAsync, type, *args, **kwargs)
        finally:
            await db.close()

    return wrapper

class PermissionsService(Service):
    async def create_permission(
        self,
        db: AsyncSession,
        name: str,
        action: str,
        description: str,
        type: str
    ) -> Permission:
        """
        Crea un solo permiso en la base de datos.
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
        self,
        db: AsyncSession,
        permissions_data: List[RQBulkPermission]
    ) -> tuple[List[RSBulkPermissionResult], int, int]:
        """
        Crea múltiples permisos y los asigna a sus roles correspondientes.
        Handles existing permissions gracefully by updating them and ensuring role links.
        """
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

    def _collect_api_routes(self, routes: List[BaseRoute]) -> List[APIRoute]:
        """Recursively collect all APIRoute instances including from nested routers."""
        from starlette.routing import Mount
        collected = []
        for route in routes:
            if isinstance(route, APIRoute):
                collected.append(route)
            elif isinstance(route, Mount) and hasattr(route, 'routes'):
                collected.extend(self._collect_api_routes(route.routes))
        return collected

    def _generate_permissions_hash(self, routes: List[APIRoute], type_name: str) -> str:
        """Generates a unique SHA256 hash based on the route attributes and permission type."""
        route_data = []
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

    async def create_permissions_api(
        self,
        routes: List[BaseRoute], sessionAsync: async_sessionmaker[AsyncSession], type: str
    ):
        db: AsyncSession = sessionAsync()
        try:
            api_routes = self._collect_api_routes(routes)
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
            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()

    def get_shield_sync_callback(self, sessionAsync: async_sessionmaker[AsyncSession]) -> Callable[[Dict[str, Any]], Any]:
        """
        Retorna la función callback que se debe proveer a Shield.scan.
        Esta función lanzará la sincronización en un job paralelo (background task).
        """
        import asyncio
        def callback(registry_dict: Dict[str, Any]):
            # Lanzamos el proceso en el background
            asyncio.create_task(self._process_shield_permissions(registry_dict, sessionAsync))
        return callback

    async def _process_shield_permissions(self, registry_dict: Dict[str, Any], sessionAsync: async_sessionmaker[AsyncSession]):
        """
        Procesa el diccionario de Shield en background, compara el hash y persiste
        los permisos nuevos en la base de datos vinculándolos al rol owner.
        """
        db: AsyncSession = sessionAsync()
        try:
            # 1. Generar hash del registro
            hash_string = json.dumps(registry_dict, sort_keys=True)
            current_hash = hashlib.sha256(hash_string.encode()).hexdigest()
            
            context_name = "system_init"
            option_name = "permissions_hash_shield"

            # 2. Check for existing hash in database
            query = await db.execute(
                select(Options).where(
                    Options.context == context_name,
                    Options.name == option_name
                )
            )
            option_record = query.scalar_one_or_none()

            if option_record and option_record.value == current_hash:
                print(f"[Shield Sync] No changes detected (Hash: {current_hash[:8]}...). Skipping sync.")
                return

            print(f"[Shield Sync] Changes detected. Syncing Shield permissions to DB...")

            # 3. Extraer todos los permisos del árbol aplanando
            all_permissions = []
            def extract_permissions(nodes_list):
                for node in nodes_list:
                    all_permissions.extend(node.get("permissions", []))
                    if "childs" in node:
                        extract_permissions(node["childs"])
            
            extract_permissions(registry_dict.get("permissions", []))

            if not all_permissions:
                print("[Shield Sync] No permissions found in scan.")
                return

            route_map = {}
            for p in all_permissions:
                # Utilizamos el nombre definido en @Shield.need(name="...")
                route_map[p["name"]] = p

            route_names = list(route_map.keys())

            # 4. Obtener permisos existentes
            existing_perms_query = await db.execute(
                select(Permission).where(Permission.name.in_(route_names))
            )
            existing_perms = {p.name: p for p in existing_perms_query.scalars().all()}

            # 5. Crear los faltantes
            new_permissions = []
            for name, p_data in route_map.items():
                if name not in existing_perms:
                    new_perm = Permission(
                        name=name,
                        action=p_data.get("action", "UNKNOWN"),
                        description=p_data.get("description", "Shield Protected Path"),
                        type=p_data.get("type", "SHIELD"),
                        context=p_data.get("context", "UNKNOWN"),
                    )
                    db.add(new_perm)
                    new_permissions.append(new_perm)

            if new_permissions:
                print(f"[Shield Sync] Creating {len(new_permissions)} new permissions...")
                await db.flush() # Flush to get IDs
                for p in new_permissions:
                    existing_perms[p.name] = p

            # 6. Vincular los permisos al rol 'owner' y manejar metadata
            owner_query = await db.execute(select(Role).where(Role.name == "owner"))
            owner_role = owner_query.scalar_one_or_none()

            all_permission_ids = [p.id for p in existing_perms.values()]
            
            # Sync Metadata
            for p_name, p_data in route_map.items():
                perm = existing_perms.get(p_name)
                if not perm or not p_data.get("meta"):
                    continue
                
                for m_key, m_val in p_data["meta"]:
                    str_val = json.dumps(m_val) if not isinstance(m_val, str) else m_val
                    # Check if exists
                    meta_check = await db.execute(
                        select(MetaPermissions).where(
                            MetaPermissions.key == m_key,
                            MetaPermissions.ref_permission == perm.id
                        )
                    )
                    existing_meta = meta_check.scalar_one_or_none()
                    if existing_meta:
                        if existing_meta.value != str_val:
                            existing_meta.value = str_val
                    else:
                        db.add(MetaPermissions(
                            key=m_key,
                            value=str_val,
                            ref_permission=perm.id
                        ))

            if owner_role:
                
                existing_links_query = await db.execute(
                    select(RolePermission.permission_id).where(
                        RolePermission.role_id == owner_role.id,
                        RolePermission.permission_id.in_(all_permission_ids)
                    )
                )
                existing_link_ids = set(existing_links_query.scalars().all())

                new_links = []
                for p_id in all_permission_ids:
                    if p_id not in existing_link_ids:
                        new_links.append(RolePermission(role_id=owner_role.id, permission_id=p_id))
                
                if new_links:
                    print(f"[Shield Sync] Linking {len(new_links)} new permissions to owner role...")
                    db.add_all(new_links)

            # 7. Actualizar o crear registro de Hash
            if option_record:
                option_record.value = current_hash
            else:
                db.add(Options(context=context_name, name=option_name, value=current_hash))

            # 8. Guardar transacción
            await db.commit()
            print(f"[Shield Sync] Shield sync completed successfully.")

        except Exception as e:
            print(f"[Shield Sync] Critical error in _process_shield_permissions: {e}")
            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()

    @injectable
    async def get_permission(
        self,
        name: str,
        context: str,
        action: str,
        type_str: str,
        db: AsyncSession = Depends(get_async_db)
    ):
        try:
            query = await db.execute(
                select(Permission).where(
                    Permission.name == name,
                    Permission.context == context,
                    Permission.action == action,
                    Permission.type == type_str
                )
            )
            return query.scalar_one_or_none()
        finally:
            await db.close()

    @injectable
    async def check_role_has_permission(
        self,
        role_id: int,
        permission_id: int,
        db: AsyncSession = Depends(get_async_db)
    ) -> bool:
        try:
            query = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                )
            )
            return query.scalar_one_or_none() is not None
        finally:
            await db.close()