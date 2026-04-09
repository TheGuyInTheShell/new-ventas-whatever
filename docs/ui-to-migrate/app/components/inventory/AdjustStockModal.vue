<script setup lang="ts">
import type { InventoryItem } from '~/composables/useInventoryQuery'

const props = defineProps<{
  open: boolean
  item: InventoryItem | null
}>()

const emit = defineEmits(['update:open', 'adjusted'])

const config = useRuntimeConfig()
const toast = useToast()

const isAdjusting = ref(false)
const formData = reactive({
  new_quantity: 0,
  is_adjustment: false, // false by default as requested
  notes: ''
})

watch(() => props.item, (newItem) => {
  if (newItem) {
    formData.new_quantity = newItem.balance || 0
    formData.is_adjustment = false
    formData.notes = ''
  }
}, { immediate: true })

async function handleSave() {
  if (!props.item) return
  isAdjusting.value = true
  
  try {
    const payload = {
      balance_id: props.item.balance_id,
      new_quantity: Number(formData.new_quantity),
      is_adjustment: formData.is_adjustment,
      notes: formData.notes
    }

    await $fetch(`${config.public.apiBase}/d/transaction_and_invoice/adjust`, {
      method: 'PUT',
      body: payload
    })

    toast.add({ title: 'Success', description: 'Stock adjusted successfully.' })
    close()
    emit('adjusted')
  } catch (error: any) {
    console.error('Adjustment failed', error)
    toast.add({ title: 'Error', description: 'Failed to adjust stock. ' + (error?.data?.detail || ''), color: 'error' })
  } finally {
    isAdjusting.value = false
  }
}

function close() {
  emit('update:open', false)
}

function onBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    close()
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click="onBackdropClick"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" />

        <!-- Dialog -->
        <div class="relative w-full max-w-md bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden" @click.stop>
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3">
              <div class="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                <UIcon name="i-lucide-arrow-right-left" class="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 class="text-lg font-semibold">
                  Adjust Stock
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ item?.name || 'Inventory Item' }}
                </p>
              </div>
            </div>
            <UButton
              icon="i-lucide-x"
              variant="ghost"
              color="neutral"
              size="sm"
              @click="close"
            />
          </div>

          <!-- Body -->
          <form class="px-6 py-5 space-y-5" @submit.prevent="handleSave">
            
            <UFormField label="New Quantity" size="lg" required>
              <UInput 
                v-model="formData.new_quantity" 
                type="number"
                step="0.01" 
              />
            </UFormField>
            
            <div class="flex items-center gap-4 pt-1">
              <USwitch size="lg" v-model="formData.is_adjustment" />
              <div class="flex flex-col">
                <span class="text-sm font-medium">Log as Adjustment</span>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ formData.is_adjustment ? 'Implicitly creates an Invoice & Transaction for accounting.' : 'Directly rewrites the balance (for fixing initial setup errors).' }}
                </span>
              </div>
            </div>

            <UFormField :ui="{ container: 'w-full' }" v-if="formData.is_adjustment" label="Reason/Notes (Optional)">
              <UTextarea :ui="{ base: 'w-full', root: 'w-full' }" 
                v-model="formData.notes" 
                placeholder="e.g. Found spare box in back... " 
              />
            </UFormField>

            <div class="flex justify-end gap-2 pt-4 border-t border-gray-200 dark:border-gray-800">
              <UButton
                label="Cancel"
                variant="outline"
                color="neutral"
                @click="close"
              />
              <UButton
                label="Save Change"
                type="submit"
                color="primary"
                :loading="isAdjusting"
                icon="i-lucide-check"
              />
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}
</style>
