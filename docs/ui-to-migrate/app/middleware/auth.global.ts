export default defineNuxtRouteMiddleware(async (to) => {
  const { isLoggedIn } = useAuth()

  // Define public routes
  const publicRoutes = ['/login', '/signup', '/auth/sign-in', '/auth/verify-otp']
  // If the user is not logged in and trying to access a restricted page
  if (!isLoggedIn.value && !publicRoutes.includes(to.path)) {
    return navigateTo('/login')
  }

  // If the user is logged in
  if (isLoggedIn.value) {
    // 1. Prevent access to login pages
    if (publicRoutes.includes(to.path)) {
      return navigateTo('/')
    }

    // Skip permission checks on server-side render (no browser cookies available)
    if (process.server) return

    // 2. Initialize permissions if not loaded
    const permissionStore = usePermissionStore()
    if (!permissionStore.loaded) {
      await permissionStore.initDetails()
    }

    // 3. Check route permission
    const { menuPermissions } = useMenuAuth()
    const requiredPerm = menuPermissions.find(p => p.meta?.route === to.path)
    if (requiredPerm) {
      // Allow bypassing checks in development until the "Seed" button is executed
      if (process.dev && permissionStore.isPermissionBypassActive) {
        console.warn(`[Dev] Bypassing permission check for ${requiredPerm.name} (Bypass Active)`)
        return
      }

      // Client-side quick check
      if (!permissionStore.hasPermission(requiredPerm.name)) {

        return abortNavigation('Insufficient permissions')
      }

      // Secure backend check (ID-based)
      const permId = permissionStore.getPermissionId(requiredPerm.name)
      if (permId) {
        try {
          const verified = await $fetch<boolean>(`/api/permissions/check/${permId}`)
          if (!verified) {
            return abortNavigation('Insufficient permissions (backend verification failed)')
          }
        } catch (error) {
          console.error('Permission check failed', error)
          return abortNavigation('Authorization check failed')
        }
      }
    }
  }
})
