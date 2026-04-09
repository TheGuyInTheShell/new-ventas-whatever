<script setup lang="ts">
import { useFiatStore } from '~/stores/useFiatStore'
import { useMenuQuery } from '~/composables/useMenuQuery'

const config = useRuntimeConfig()
const toast = useToast()
const fiatStore = useFiatStore()

// Data
const { items: dishes, isLoading: loading } = useMenuQuery()

// Cart
const cart = ref<any[]>([])
const isCheckoutOpen = ref(false)
const selectedPaymentMethod = ref<number | null>(null)

onMounted(async () => {
  await fiatStore.fetchFiats()
  selectedPaymentMethod.value = fiatStore.mainFiatId
})

function addToCart(dish: any) {
  const existing = cart.value.find(item => item.id === dish.id)
  if (existing) {
    existing.quantity++
  } else {
    cart.value.push({ ...dish, quantity: 1 })
  }
}

function removeFromCart(index: number) {
  cart.value.splice(index, 1)
}

function updateQuantity(index: number, delta: number) {
  const item = cart.value[index]
  item.quantity += delta
  if (item.quantity <= 0) {
    removeFromCart(index)
  }
}

const cartTotal = computed(() => {
  return cart.value.reduce((sum, item) => sum + (item.price * item.quantity), 0)
})

const mainCurrency = computed(() => {
  return fiatStore.fiats.find(f => f.id === fiatStore.mainFiatId)?.expression || '$'
})

async function processSale() {
  if (!selectedPaymentMethod.value) {
    toast.add({ title: 'Error', description: 'Select a payment method', color: 'error' })
    return
  }

  try {
    const payload = {
      items: cart.value.map(item => ({
        id: item.id,
        quantity: item.quantity
      })),
      payment_method_id: selectedPaymentMethod.value
    }

    await $fetch(`${config.public.apiBase}/transactions/sale`, {
      method: 'POST',
      body: payload
    })

    toast.add({ title: 'Success', description: 'Sale processed' })
    cart.value = []
    isCheckoutOpen.value = false
  } catch (error) {
    console.error('Sale failed', error)
    toast.add({ title: 'Error', description: 'Sale processing failed', color: 'error' })
  }
}

const paymentOptions = computed(() => {
  return fiatStore.fiats.map(f => ({ label: f.name, value: f.id }))
})
</script>

<template>
  <div class="h-[calc(100vh-64px)] flex gap-4 p-4 overflow-hidden w-full">
    <!-- Menu Grid -->
    <div class="grow overflow-y-auto pr-2">
      <h1 class="text-2xl font-bold mb-4">
        Sales Register
      </h1>

      <div v-if="loading" class="flex justify-center py-8">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl" />
      </div>

      <div v-else class="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-4">
        <div
          v-for="dish in dishes"
          :key="dish.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow cursor-pointer hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden"
          @click="addToCart(dish)"
        >
          <div class="card-dish aspect-video bg-gray-100 dark:bg-gray-900 overflow-hidden relative border-b border-gray-200 dark:border-gray-800">
            <img v-if="dish.image_id" :src="dish.image_id" class="w-full h-full object-cover" alt="Dish image" />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
              <UIcon name="i-lucide-image" class="w-8 h-8 opacity-50" />
            </div>
          </div>
          <div class="p-2 flex flex-col gap-1">
            <h3 class="font-bold text-base truncate">
              {{ dish.name }}
            </h3>
            <p v-if="dish.prep_time" class="text-xs text-gray-500 truncate">
              {{ dish.prep_time }}
            </p>
            <div class="text-right font-bold text-primary-600 dark:text-primary-400 mt-1">
              {{ dish.price }} {{ dish.currency }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Cart Sidebar -->
    <div class="w-96 bg-gray-50 dark:bg-gray-900 rounded-lg shadow-inner flex flex-col p-4 border border-gray-200 dark:border-gray-700">
      <h2 class="text-xl font-bold mb-4">
        Current Sale
      </h2>

      <div class="grow overflow-y-auto space-y-2 mb-4">
        <div v-if="cart.length === 0" class="text-center text-gray-500 py-8">
          Cart is empty
        </div>
        <div v-for="(item, index) in cart" :key="index" class="bg-white dark:bg-gray-800 p-3 rounded shadow-sm flex items-center gap-2">
          <div class="grow">
            <div class="font-bold">
              {{ item.name }}
            </div>
            <div class="text-xs text-gray-500">
              {{ item.price }} {{ item.currency }} x {{ item.quantity }}
            </div>
          </div>
          <div class="flex items-center gap-1">
            <UButton
              icon="i-lucide-minus"
              size="xs"
              color="neutral"
              variant="ghost"
              @click.stop="updateQuantity(index, -1)"
            />
            <span class="w-6 text-center text-sm">{{ item.quantity }}</span>
            <UButton
              icon="i-lucide-plus"
              size="xs"
              color="neutral"
              variant="ghost"
              @click.stop="updateQuantity(index, 1)"
            />
          </div>
          <div class="font-semibold w-16 text-right">
            {{ (item.price * item.quantity).toFixed(2) }}
          </div>
        </div>
      </div>

      <div class="border-t pt-4 space-y-4">
        <div class="flex justify-between items-center text-xl font-bold">
          <span>Total</span>
          <span>{{ cartTotal.toFixed(2) }} {{ mainCurrency }}</span>
        </div>

        <UButton
          block
          size="xl"
          label="Checkout"
          :disabled="cart.length === 0"
          @click="isCheckoutOpen = true"
        />
      </div>
    </div>

    <!-- Checkout Modal -->
    <UModal v-model="isCheckoutOpen">
      <UCard :ui="{ header: 'flex justify-between items-center' }">
        <template #header>
          <h3 class="text-lg font-bold">
            Complete Sale
          </h3>
          <UButton icon="i-lucide-x" variant="ghost" @click="isCheckoutOpen = false" />
        </template>

        <div class="space-y-4">
          <div class="text-center py-4">
            <div class="text-sm text-gray-500">
              Total to Pay
            </div>
            <div class="text-4xl font-bold">
              {{ cartTotal.toFixed(2) }} {{ mainCurrency }}
            </div>
          </div>

          <UFormField label="Payment Method" required>
            <USelect
              v-model="selectedPaymentMethod"
              :options="paymentOptions"
              placeholder="Select payment method"
            />
          </UFormField>

          <div class="flex justify-end pt-4">
            <UButton
              label="Process Payment"
              size="lg"
              block
              :loading="loading"
              @click="processSale"
            />
          </div>
        </div>
      </UCard>
    </UModal>
  </div>
</template>

<style scoped>
.card-dish {
  height: 100%;
  max-height: 240px;
}
</style>
