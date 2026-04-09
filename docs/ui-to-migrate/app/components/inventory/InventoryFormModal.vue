<script setup lang="ts">
import { useFiatStore } from '~/stores/useFiatStore'
import type { InventoryItem, RQValueWithComparison } from '~/composables/useInventoryQuery'

const props = defineProps<{
  open: boolean
  editingItem?: InventoryItem | null
  saveMutation?: any 
}>()

const emit = defineEmits(['update:open', 'saved'])

const fiatStore = useFiatStore()

const types = ['ingredient', 'utensil', 'consumable', 'other']

const formData = reactive({
  name: '',
  type: 'ingredient',
  expression: 'unit',
  price: 0,
  currency_id: null as number | null
})

const mainFiatName = computed(() => {
  const fiat = fiatStore.fiats.find((f) => f.id === fiatStore.mainFiatId)
  return fiat?.name || 'Main Currency'
})

watch(() => props.editingItem, (item) => {
  if (item) {
    formData.name = item.name
    formData.type = item.type
    formData.expression = item.expression
    formData.price = item.price || 0
    formData.currency_id = item.currency_id || fiatStore.mainFiatId
  } else {
    formData.name = ''
    formData.type = 'ingredient'
    formData.expression = 'unit'
    formData.price = 0
    formData.currency_id = fiatStore.mainFiatId
  }
}, { immediate: true })

const isSaving = ref(false)

async function handleSave() {
  if (!props.saveMutation) return
  isSaving.value = true
  try {
    const payloadToSave: RQValueWithComparison = {
      value: {
        name: formData.name,
        type: formData.type,
        expression: formData.expression,
        context: 'chinese_restaurant'
      },
      comparison_value: {
        quantity_from: 1,
        quantity_to: formData.price,
        value_to: formData.currency_id,
        context: 'chinese_restaurant'
      },
      business_entity_ids: [1]
    }
    
    await props.saveMutation.mutateAsync({
      editingItem: props.editingItem,
      formData: payloadToSave
    })
    close()
    emit('saved')
  } catch {
    // Error handled by mutation's onError callback
  } finally {
    isSaving.value = false
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
        <div class="relative w-full max-w-lg bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden" @click.stop>
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3">
              <div class="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                <UIcon :name="editingItem ? 'i-lucide-edit' : 'i-lucide-package-plus'" class="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 class="text-lg font-semibold">
                  {{ editingItem ? 'Edit Item' : 'New Item' }}
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ editingItem ? 'Update inventory details' : 'Add to your inventory' }}
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
            <UFormField label="Item Name" required>
              <UInput v-model="formData.name" placeholder="e.g. Soy Sauce, Wok Pan..." size="lg" />
            </UFormField>

            <div class="grid grid-cols-2 gap-4">
              <UFormField label="Category" required>
                <USelect v-model="formData.type" :options="types" size="lg" />
              </UFormField>

              <UFormField label="Unit" required>
                <UInput v-model="formData.expression" placeholder="kg, unit, l" size="lg" />
              </UFormField>
            </div>

            <USeparator label="Pricing" />

            <div class="grid grid-cols-2 gap-4">
              <UFormField label="Price">
                <UInput
                  v-model="formData.price"
                  type="number"
                  step="0.01"
                  size="lg"
                  placeholder="0.00"
                />
              </UFormField>

              <UFormField label="Currency ID">
                <USelect
                  v-model="formData.currency_id"
                  :options="fiatStore.fiats.map((f) => ({ label: f.name, value: f.id }))"
                  placeholder="Select currency"
                  size="lg"
                />
                <span class="text-xs text-gray-600 dark:text-gray-400 pl-2">{{ Object.entries(fiatStore.fiats.find((f) => f.id === formData.currency_id) || {}).map(([key, value]) => { if (key === 'name') return value; if (key === 'expression') return `(${value})`; }).join(' ') }}</span>
              </UFormField>
            </div>

            <div v-if="mainFiatName" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary/5 border border-primary/10">
              <UIcon name="i-lucide-info" class="w-4 h-4 text-primary shrink-0" />
              <span class="text-xs text-gray-600 dark:text-gray-400">
                Main currency: <strong class="text-primary">{{ mainFiatName }}</strong>
              </span>
            </div>

            <div class="flex justify-end gap-2 pt-2">
              <UButton
                label="Cancel"
                variant="outline"
                color="neutral"
                @click="close"
              />
              <UButton
                label="Save"
                type="submit"
                color="primary"
                :loading="isSaving"
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
