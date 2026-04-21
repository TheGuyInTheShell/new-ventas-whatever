from core.security.shield import Shield, ShieldGroup


# ---------------------------------------------------------------------------
# Children classes — permisos hijos de cada sección del menú
# ---------------------------------------------------------------------------

class ChineseRestaurantChildren:
    menu = Shield.can(
        "chinese_restaurant.menu",
        "read",
        "ui",
        description="Ver el menú del restaurante chino",
        meta=[("icon", "mdi-food-fork-drink")],
    )
    orders = Shield.can(
        "chinese_restaurant.orders",
        "read",
        "ui",
        description="Ver los pedidos del restaurante chino",
        meta=[("icon", "mdi-clipboard-list")],
    )
    tables = Shield.can(
        "chinese_restaurant.tables",
        "read",
        "ui",
        description="Ver las mesas del restaurante chino",
        meta=[("icon", "mdi-table-chair")],
    )
    staff = Shield.can(
        "chinese_restaurant.staff",
        "read",
        "ui",
        description="Ver el personal del restaurante chino",
        meta=[("icon", "mdi-account-tie")],
    )
    reservations = Shield.can(
        "chinese_restaurant.reservations",
        "read",
        "ui",
        description="Ver las reservaciones del restaurante chino",
        meta=[("icon", "mdi-calendar-clock")],
    )


class SettingsChildren:
    users = Shield.can(
        "settings.users",
        "read",
        "ui",
        description="Gestión de usuarios del sistema",
        meta=[("icon", "mdi-account")],
    )
    roles = Shield.can(
        "settings.roles",
        "read",
        "ui",
        description="Gestión de roles del sistema",
        meta=[("icon", "mdi-account-group")],
    )
    permissions = Shield.can(
        "settings.permissions",
        "read",
        "ui",
        description="Gestión de permisos del sistema",
        meta=[("icon", "mdi-lock")],
    )
    fiat_config = Shield.can(
        "settings.fiat_config",
        "read",
        "ui",
        description="Configuración de monedas FIAT",
        meta=[("icon", "mdi-currency-usd")],
    )


# ---------------------------------------------------------------------------
# Árbol raíz del menú de la aplicación
# ---------------------------------------------------------------------------

class MenuShields(ShieldGroup):
    """
    Árbol de permisos de UI para el menú principal de la aplicación.

    Al ser importado, registra automáticamente todos sus permisos en el
    PermissionRegistry global.

    Uso::

        MenuShields.to_dict()     # schema del registry (para el gestor de permisos)
        MenuShields.to_consume()  # schema simplificado (para el frontend)
    """

    __context__ = "Menu"

    chinese_restaurant = Shield.can(
        "chinese_restaurant",
        "read",
        "ui",
        description="Acceso al módulo de restaurante chino",
        meta=[("icon", "mdi-food-fork-drink")],
    ).children(ChineseRestaurantChildren)

    settings = Shield.can(
        "settings",
        "read",
        "ui",
        description="Acceso al módulo de configuración del sistema",
        meta=[("icon", "mdi-cog")],
    ).children(SettingsChildren)

    profile = Shield.can(
        "profile",
        "read",
        "ui",
        description="Acceso al perfil de usuario",
        meta=[("icon", "mdi-account")],
    )
