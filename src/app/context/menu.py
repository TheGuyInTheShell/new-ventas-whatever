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
        meta=[
            ("icon", "utensils"),
            ("route", "/dashboard/chinese-restaurant/menu"),
            ("name", "Menú"),
        ],
    )
    orders = Shield.can(
        "chinese_restaurant.orders",
        "read",
        "ui",
        description="Ver los pedidos del restaurante chino",
        meta=[
            ("icon", "clipboard-list"),
            ("route", "/dashboard/chinese-restaurant/orders"),
            ("name", "Pedidos"),
        ],
    )
    tables = Shield.can(
        "chinese_restaurant.tables",
        "read",
        "ui",
        description="Ver las mesas del restaurante chino",
        meta=[
            ("icon", "table"),
            ("route", "/dashboard/chinese-restaurant/tables"),
            ("name", "Mesas"),
        ],
    )
    staff = Shield.can(
        "chinese_restaurant.staff",
        "read",
        "ui",
        description="Ver el personal del restaurante chino",
        meta=[
            ("icon", "contact"),
            ("route", "/dashboard/chinese-restaurant/staff"),
            ("name", "Personal"),
        ],
    )
    reservations = Shield.can(
        "chinese_restaurant.reservations",
        "read",
        "ui",
        description="Ver las reservaciones del restaurante chino",
        meta=[
            ("icon", "calendar-clock"),
            ("route", "/dashboard/chinese-restaurant/reservations"),
            ("name", "Reservaciones"),
        ],
    )


class SettingsChildren:
    users = Shield.can(
        "settings.users",
        "read",
        "ui",
        description="Gestión de usuarios del sistema",
        meta=[
            ("icon", "user"),
            ("route", "/dashboard/settings/users"),
            ("name", "Usuarios"),
        ],
    )
    roles = Shield.can(
        "settings.roles",
        "read",
        "ui",
        description="Gestión de roles del sistema",
        meta=[
            ("icon", "users"),
            ("route", "/dashboard/settings/roles"),
            ("name", "Roles"),
        ],
    )
    permissions = Shield.can(
        "settings.permissions",
        "read",
        "ui",
        description="Gestión de permisos del sistema",
        meta=[
            ("icon", "lock"),
            ("route", "/dashboard/settings/permissions"),
            ("name", "Permisos"),
        ],
    )
    fiat_config = Shield.can(
        "settings.fiat_config",
        "read",
        "ui",
        description="Configuración de monedas FIAT",
        meta=[
            ("icon", "circle-dollar-sign"),
            ("route", "/dashboard/settings/fiat-config"),
            ("name", "Monedas FIAT"),
        ],
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
        meta=[
            ("icon", "utensils"),
            ("route", "/dashboard/chinese-restaurant"),
            ("name", "Restaurante Chino"),
        ],
    ).children(ChineseRestaurantChildren)

    settings = Shield.can(
        "settings",
        "read",
        "ui",
        description="Acceso al módulo de configuración del sistema",
        meta=[
            ("icon", "cog"),
            ("route", "/dashboard/settings"),
            ("name", "Configuración"),
        ],
    ).children(SettingsChildren)

    profile = Shield.can(
        "profile",
        "read",
        "ui",
        description="Acceso al perfil de usuario",
        meta=[
            ("icon", "user"),
            ("route", "/dashboard/profile"),
            ("name", "Perfil"),
        ],
    )
