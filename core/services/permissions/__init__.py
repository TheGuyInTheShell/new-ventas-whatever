from typing import TypeVar, Dict

class PermissionNode:
    context: str
    name: str
    action: str
    permission_meta: dict
    child: "PermissionNode"


T = TypeVar('T')

class PermissionsTree:

    permissions_tree: Dict[str, "PermissionNode"] = {}

    """
    return the unique and deterministic sign of all permissions ordened, this help to not repeat the creation in the database
    """
    def get_sign(self) -> str:
        return ""


    "get all permissions ordened"
    def get_all(self):
        return set

    def register(self, context: str, name: str, action: str) -> "PermissionNode":

        return PermissionNode()

    def append_child(self, parent_permission: "PermissionNode", child_permission: "PermissionNode"):
        pass

    def can(self, context: str, name: str, action: str):
        return True
    
    def find_permission_in_tree(self, context: str, name: str, action: str):
        return PermissionNode()