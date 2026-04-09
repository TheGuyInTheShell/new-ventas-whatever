import { useBusinessEntityStore } from '~/stores/useBusinessEntityStore'

export default defineNuxtPlugin(() => {
  // Only run on client side and in development (if needed/desired)
  onNuxtReady(async () => {
    if (process.dev) {
      console.log('[Auth Plugin] Seeding permissions...')
      const businessEntityStore = useBusinessEntityStore()
      await businessEntityStore.seedBusinessChineseRestaurant()
    }
  })
})
