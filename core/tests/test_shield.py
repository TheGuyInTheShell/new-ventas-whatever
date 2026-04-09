import pytest
import os
import sys
from typing import Any

from core.security.shield import (
    Shield, 
    ShieldPermissionError, 
    ShieldRegistryError, 
    ResolverProvider,
    PermissionDefinition
)
from core.security.shield.registry import permission_registry

# --- Fixtures y Utils ---

@pytest.fixture(autouse=True)
def clean_registry():
    """Limpia el registro antes y despues de cada test."""
    permission_registry.clear()
    yield
    permission_registry.clear()

class MockProvider(ResolverProvider):
    def __init__(self, allowed: bool):
        self.allowed = allowed
    
    def resolve(self, name: str, type_str: str, action: str, context: str, **kwargs: Any) -> bool:
        return self.allowed

# --- Tests de Registro Manual e Imperativo ---

def test_shield_create():
    Shield.create(
        name="test:manual",
        action="create",
        type="action",
        description="A manual permission",
        context="GlobalContext",
        meta=("module", "tests")
    )
    
    # check if it ended up in registry under "GlobalContext"
    node = permission_registry.get_node("GlobalContext")
    assert node is not None
    assert len(node.permissions) == 1
    assert node.permissions[0].name == "test:manual"
    assert node.permissions[0].meta.key == "module"
    assert node.permissions[0].meta.value == "tests"

def test_shield_create_duplication_fails():
    Shield.create(name="test:dup", action="create", type="action", description="1", context="Ctx")
    with pytest.raises(ShieldRegistryError):
        Shield.create(name="test:dup", action="create", type="action", description="2", context="Ctx")

def test_shield_use_allows_execution():
    provider = MockProvider(allowed=True)
    
    executed = False
    def my_action():
        nonlocal executed
        executed = True
        return "Success"
        
    result = Shield.use(name="test:action", action="execute", type="action", context="Ctx")(provider, my_action)
    
    assert executed
    assert result == "Success"

def test_shield_use_denies_execution():
    provider = MockProvider(allowed=False)
    
    def my_action():
        return "Success"
        
    with pytest.raises(ShieldPermissionError) as exc_info:
        Shield.use(name="test:action", action="execute", type="action", context="Ctx")(provider, my_action)
        
    assert exc_info.value.name == "test:action"
    assert exc_info.value.context == "Ctx"
    assert "No permission for 'test:action'" in str(exc_info.value)

# --- Tests de Decoradores (Clase y Metodo) ---

from core.lib.decorators import Get

@Shield.register
class ExampleController:
    @Shield.need(name="example:read", action="read", type="endpoint", description="Read example")
    def read(self):
        pass

@Shield.register(context="CustomContext")
class CustomContextController:
    @Get("/custom")
    @Shield.need(name="custom:read", action="read", type="endpoint", description="Custom read")
    def read(self):
        pass
    
    def unannotated(self):
        pass

def test_shield_decorators_inject_metadata():
    assert getattr(ExampleController, "__shield_context_marker__") is True
    assert getattr(ExampleController, "__shield_context__") is None  # no explicit context

    assert getattr(CustomContextController, "__shield_context_marker__") is True
    assert getattr(CustomContextController, "__shield_context__") == "CustomContext"
    
    perms = getattr(CustomContextController.read, "__shield_permissions__")
    assert len(perms) == 1
    assert perms[0]["name"] == "custom:read"
    assert perms[0]["context"] is None # hereda el de la clase en tiempo de escaneo

    # Verification of dependency injection
    deps = getattr(ExampleController.read, "__dependencies__")
    assert len(deps) == 1
    assert deps[0].__class__.__name__ == "Depends"

    # Verification of integration with Core HTTP decorator (`@Get`)
    route_def = getattr(CustomContextController.read, "__route_definition__")
    assert route_def is not None
    assert "dependencies" in route_def.kwargs
    assert len(route_def.kwargs["dependencies"]) == 1
    assert route_def.kwargs["dependencies"][0].__class__.__name__ == "Depends"

# --- Tests de Shield ARG ---

def test_shield_arg_descriptor():
    marker = Shield.arg(
        name="test:arg", 
        action="read",
        type="argument", 
        description="Arg desc",
        default="DefaultValue",
        context="ArgCtx",
        meta=("k", "v")
    )
    
    assert hasattr(marker, "__shield_arg__")
    assert marker.name == "test:arg"
    assert marker.default == "DefaultValue"
    assert marker.context == "ArgCtx"

# --- Tests de Scanner y Arbol Jerárquico ---

def test_shield_scan_resolves_and_builds_tree(tmp_path):
    # Crear un modulo temporal en el file system para que lo lea el scanner
    d = tmp_path / "src"
    d.mkdir()
    p = d / "fake_controller.py"
    
    content = '''
from core.security.shield import Shield

@Shield.register(context="ModuleA")
class ModuleAController:
    @Shield.need(name="modA:read", action="read", type="endpoint", description="Read A")
    def read(self): pass

@Shield.register  # Tomara el contexto default del scan o fallback
class ModuleBController:
    @Shield.need(name="modB:read", action="read", type="endpoint", description="Read B")
    def read(self): pass
    
    @Shield.need(name="custom:op", action="execute", type="endpoint", description="C", context="OverrideCtx")
    def op(self): pass
'''
    p.write_text(content)
    
    latest_dict = {}
    def receiver(d: dict):
        nonlocal latest_dict
        latest_dict = d

    # El scanner le pasa contexto global AppBase. 
    # El archivo se carga, ModuleA impone su propio context ("ModuleA")
    # ModuleB no impone contexto, asi que toma "AppBase".
    # Y `op` impone "OverrideCtx", que colgando de "AppBase", se une
    Shield.scan(str(d), receiver, context="AppBase")
    
    # El arbol reconstruido a nivel global (de root) deberia tener "AppBase", "ModuleA"
    assert "permissions" in latest_dict
    
    import json
    print("\n--- DICCIONARIO DE PERMISOS GENERADO ---")
    print(json.dumps(latest_dict, indent=2, default=str))
    print("----------------------------------------\n")

    
    # Check "AppBase" via directly querying the index as well for sanity
    app_base_node = permission_registry.get_node("AppBase")
    assert app_base_node is not None
    assert len(app_base_node.permissions) == 1
    assert app_base_node.permissions[0].name == "modB:read"
    assert app_base_node.permissions[0].context == "AppBase"
    
    # Check OverrideCtx que fue colgado al AppBase ya que era el contexto default
    assert "OverrideCtx" in app_base_node.childs
    override_node = app_base_node.childs["OverrideCtx"]
    assert len(override_node.permissions) == 1
    assert override_node.permissions[0].name == "custom:op"
    
    # ModuleA fue insertado en el vacio o colgado del root porque declaro propio context pero sin padre explicito global
    module_a_node = permission_registry.get_node("ModuleA")
    assert module_a_node is not None
    assert module_a_node.permissions[0].name == "modA:read"

def test_clean_registry_empties_everything():
    Shield.create("test", "create", "t", "d", "c")
    assert permission_registry.get_node("c") is not None
    permission_registry.clear()
    assert permission_registry.get_node("c") is None
