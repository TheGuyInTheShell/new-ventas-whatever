export interface PermissionDefinition {
  name: string
  action: string // GET, POST, etc. or VIEW for menus
  description: string
  type: string // 'MENU', 'API', 'UI'
  meta?: Record<string, any>
}

export const menuPermissions: PermissionDefinition[] = [
  {
    name: 'VIEW_DASHBOARD',
    action: 'VIEW',
    description: 'Access to Dashboard',
    type: 'MENU',
    meta: {
      label: 'Dashboard',
      icon: 'i-lucide-layout-dashboard',
      route: '/',
      order: 1
    }
  },
  {
    name: 'VIEW_CHINESE_RESTAURANT',
    action: 'VIEW',
    description: 'Access to Chinese Restaurant',
    type: 'MENU',
    meta: {
      label: 'Chinese Restaurant',
      icon: 'i-lucide-utensils',
      route: '/chinese-restaurant',
      order: 2,
      submenu: JSON.stringify([
        {
          label: 'Dashboard',
          icon: 'i-lucide-layout-dashboard',
          route: '/chinese-restaurant'
        },
        {
          label: 'Inventory',
          icon: 'i-lucide-package',
          route: '/chinese-restaurant/inventory'
        },
        {
          label: 'Menu',
          icon: 'i-lucide-book-open',
          route: '/chinese-restaurant/menu'
        },
        {
          label: 'Sales',
          icon: 'i-lucide-shopping-cart',
          route: '/chinese-restaurant/sales'
        },
        {
          label: 'Settings',
          icon: 'i-lucide-settings',
          route: '/chinese-restaurant/settings'
        }
      ])
    }
  },
  {
    name: 'VIEW_USERS',
    action: 'VIEW',
    description: 'Access to User Management',
    type: 'MENU',
    meta: {
      label: 'Users',
      icon: 'i-lucide-users',
      route: '/users',
      order: 3
    }
  },
  {
    name: 'VIEW_SETTINGS',
    action: 'VIEW',
    description: 'Access to Settings',
    type: 'MENU',
    meta: {
      label: 'Settings',
      icon: 'i-lucide-settings',
      route: '/settings',
      order: 4,
      submenu: JSON.stringify([
        {
          label: 'Fiat',
          icon: 'i-lucide-settings-2',
          route: '/settings/fiat'
        },
        {
          label: 'Security',
          icon: 'i-lucide-shield-check',
          route: '/settings/security'
        }
      ])
    }
  }
]

export const useMenuAuth = () => {
  return {
    menuPermissions
  }
}
