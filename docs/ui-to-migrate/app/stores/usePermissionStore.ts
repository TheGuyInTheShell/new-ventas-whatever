import { defineStore } from 'pinia'
import { useMenuAuth } from '../composables/useMenuAuth'
import { useViewAuth } from '../composables/useViewAuth'

export interface PermissionNode {
  id: number
  name: string
  action: string
  description: string
  type: string
  meta: Record<string, any>
  children?: PermissionNode[]
}

interface PermissionState {
  menu: PermissionNode[]
  permissions: string[]
  permissionMap: Record<string, number>
  loaded: boolean
  roleId: number | null
  roleName: string | null
  isPermissionBypassActive: boolean
}

export const usePermissionStore = defineStore('permissions', {
  state: (): PermissionState => ({
    menu: [],
    permissions: [],
    permissionMap: {},
    loaded: false,
    roleId: null,
    roleName: null,
    isPermissionBypassActive: process.dev // Default bypass to true in Dev
  }),

  actions: {
    async initDetails() {
      if (this.loaded) return
      // Fetch user permissions
      await this.fetchUserPermissions()
    },

    async seedPermissions() {
      const { menuPermissions } = useMenuAuth()
      const { viewPermissions } = useViewAuth()
      const config = useRuntimeConfig()

      // Default to fetched roleId or fallback to 1 (owner) for seeding
      const ownerRoleId = this.roleId || 1

      // Prepare payload
      const payload = {
        permissions: [
          ...menuPermissions.map(p => ({
            ...p,
            role_id: ownerRoleId
          })),
          ...viewPermissions.map(p => ({
            ...p,
            role_id: ownerRoleId
          }))
        ]
      }

      try {
        if (process.dev) {
          const token = useCookie('access_token')
          if (token.value) {
            // Keep bypass active during seeding to avoid being kicked out
            this.isPermissionBypassActive = true

            await $fetch(`${config.public.apiBase}/permissions/bulk`, {
              method: 'POST',
              body: payload,
              headers: {
                Authorization: `Bearer ${token.value}`
              }
            })

            // On success, enforce permissions
            this.isPermissionBypassActive = false
            console.log('[Dev] Seeding complete. Permission checks are now ACTIVE.')

            // Fully reload permissions
            this.loaded = false
            await this.initDetails()
          }
        }
      } catch (error) {
        console.error('Failed to seed permissions:', error)
      }
    },

    async fetchUserPermissions() {
      try {
        const config = useRuntimeConfig()
        const response: any = await $fetch(`${config.public.apiBase}/users/me`)

        // response.permissions is List[RSPermission{id, name, meta...}]
        const userPerms = response.permissions || []
        this.roleId = response.role || null
        this.roleName = response.role_name || null

        console.log(userPerms)
        // 1. Build Permission Map
        this.permissionMap = {}
        this.permissions = []
        userPerms.forEach((p: any) => {
          this.permissionMap[p.name] = p.id
          this.permissions.push(p.name)
        })

        // 2. Build Menu Tree
        const { menuPermissions } = useMenuAuth()

        const validMenuNodes: PermissionNode[] = []

        for (const def of menuPermissions) {
          // Show menu if user has permission OR if bypass is active (Dev only)
          const hasPerm = this.permissions.includes(def.name)
          const shouldShow = hasPerm || this.isPermissionBypassActive

          if (def.type === 'MENU' && shouldShow) {
            const permId = this.permissionMap[def.name]
            const backendPerm = userPerms.find((p: any) => p.name === def.name)

            // Merge client def with backend meta
            const mergedMeta = { ...def.meta, ...(backendPerm?.meta || {}) }

            // 3. Process Embedded Submenus
            let children: PermissionNode[] = []
            if (mergedMeta.submenu) {
              try {
                const submenuData = typeof mergedMeta.submenu === 'string'
                  ? JSON.parse(mergedMeta.submenu)
                  : mergedMeta.submenu

                if (Array.isArray(submenuData)) {
                  children = submenuData.map((item: any) => ({
                    id: 0, // Embedded items don't have IDs in this schema
                    name: item.label, // Use label as fallback name
                    action: 'VIEW',
                    description: item.label,
                    type: 'SUBMENU_ITEM',
                    meta: {
                      label: item.label,
                      icon: item.icon,
                      route: item.route
                    },
                    children: []
                  }))
                }
              } catch (e) {
                console.error('Error parsing embedded submenu for', def.name, e)
              }
            }

            const node: PermissionNode = {
              id: permId || 0,
              name: def.name,
              action: def.action,
              description: def.description,
              type: def.type,
              meta: mergedMeta,
              children: children
            }

            validMenuNodes.push(node)
          }
        }

        // Sort by client-side order
        validMenuNodes.sort((a, b) => (a.meta.order || 0) - (b.meta.order || 0))

        this.menu = validMenuNodes
        this.loaded = true
      } catch (error) {
        console.error('Error fetching user permissions:', error)
      }
    },

    hasPermission(name: string): boolean {
      return this.permissions.includes(name)
    },

    getPermissionId(name: string): number | undefined {
      return this.permissionMap[name]
    }
  },

  getters: {
    sidebarLinks(): any[] {
      return this.menu.map((node) => {
        const children = node.children && node.children.length > 0
          ? node.children.map(child => ({
            label: child.meta.label || child.name,
            to: child.meta.route || '#',
            icon: child.meta.icon
          }))
          : undefined

        return {
          label: node.meta.label || node.name,
          icon: node.meta.icon,
          to: node.meta.route || (children ? undefined : '#'),
          children: children
        }
      })
    }
  },
})
