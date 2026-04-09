<script setup lang="ts">
import { boolean } from 'zod'
import { useFiatStore } from '~/stores/useFiatStore'

const fiatStore = useFiatStore()

const toast = useToast()

// Fiat Logic
const newFiat = reactive({
  name: '',
  expression: '',
  loadPayload: false
})
onMounted(async () => {
  await fiatStore.fetchExchangeRates()
})

const isAddingFiat = ref(false)
async function onAddFiat() {
  if (newFiat.name && newFiat.expression) {
    isAddingFiat.value = true
    try {
      await fiatStore.createFiat(newFiat.name, newFiat.expression)
      newFiat.name = ''
      newFiat.expression = ''
    } finally {
      isAddingFiat.value = false
    }
  }
}

const settingMainId = ref<number | null>(null)
async function onSetMainFiat(id: number) {
  settingMainId.value = id
  try {
    await fiatStore.setMainFiat(id)
  } finally {
    settingMainId.value = null
  }
}

const isSettingRate = ref<number | null>(null)
async function onSetRate(fiatId: number) {
  if (fiatStore.mainFiatId && fiatStore.exchangeRates[fiatId]) {
    isSettingRate.value = fiatId
    try {
      // 1 Main = Rate Other, context = 'main'
      await fiatStore.createLink(fiatStore.mainFiatId, fiatId, fiatStore.exchangeRates[fiatId], 'main')
    } finally {
      isSettingRate.value = null
    }
  }
}

const mainFiatOptions = computed(() => {
  return fiatStore.fiats.map(f => ({ label: f.name, value: f.id }))
})

// Delete Logic
const deleteModalOpen = ref(false)
const fiatToDelete = ref<any>(null)

function openDeleteModal(fiat: any) {
  fiatToDelete.value = fiat
  deleteModalOpen.value = true
}

const isDeletingFiat = ref(false)
async function confirmDelete() {
  if (fiatToDelete.value) {
    isDeletingFiat.value = true
    try {
      await fiatStore.deleteFiat(fiatToDelete.value.id)
      deleteModalOpen.value = false
      fiatToDelete.value = null
    } finally {
      isDeletingFiat.value = false
    }
  }
}

// Custom Comparisons Logic
const newComparison = reactive({
  fromId: null as number | null,
  toId: null as number | null,
  rate: null as number | null,
  loadPayload: false
})

const customComparisons = computed(() => {
  return fiatStore.comparisons.filter((comp: any) => {
    return comp.context === 'custom'
  })
})

const compRates = reactive<Record<number, number>>({})

watch(() => fiatStore.comparisons, (comps) => {
  if (!comps) return
  comps.forEach((comp: any) => {
    if (!compRates[comp.id]) {
      compRates[comp.id] = comp.quantity_to / comp.quantity_from
    }
  })
}, { immediate: true })

function getFiatName(id: number) {
  const fiat = fiatStore.fiats.find((f: any) => f.id === id)
  return fiat ? fiat.name : `#${id}`
}

function getFiatExpression(id: number) {
  const fiat = fiatStore.fiats.find((f: any) => f.id === id)
  return fiat ? fiat.expression : ''
}

const isAddingComparison = ref(false)
async function onAddComparison() {
  if (newComparison.fromId && newComparison.toId && newComparison.rate) {
    if (newComparison.fromId === newComparison.toId) {
      toast.add({ title: 'Error', description: 'Cannot compare a currency with itself', color: 'error' })
      return
    }
    isAddingComparison.value = true
    try {
      await fiatStore.createLink(newComparison.fromId, newComparison.toId, newComparison.rate, 'custom')
      newComparison.fromId = null
      newComparison.toId = null
      newComparison.rate = null
    } finally {
      isAddingComparison.value = false
    }
  }
}

const updatingCompId = ref<number | null>(null)
async function onUpdateCompRate(comp: any) {
  const rate = compRates[comp.id]
  if (rate && rate > 0) {
    updatingCompId.value = comp.id
    try {
      await fiatStore.updateComparison(comp.id, comp.value_from, comp.value_to, rate, 'custom')
    } finally {
      updatingCompId.value = null
    }
  }
}

const deleteCompModalOpen = ref(false)
const compToDelete = ref<any>(null)

function openDeleteCompModal(comp: any) {
  compToDelete.value = comp
  deleteCompModalOpen.value = true
}

const isDeletingComp = ref(false)
async function confirmDeleteComp() {
  if (compToDelete.value) {
    isDeletingComp.value = true
    try {
      await fiatStore.deleteComparison(compToDelete.value.id)
      deleteCompModalOpen.value = false
      compToDelete.value = null
    } finally {
      isDeletingComp.value = false
    }
  }
}
</script>

<template>
  <div class="relative">
    <!-- Global Loading Overlay -->
    <div v-if="fiatStore.loading" class="absolute inset-0 z-50 flex items-center justify-center bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm rounded-xl">
      <div class="flex flex-col items-center gap-3">
        <UIcon name="i-lucide-loader-2" class="w-10 h-10 animate-spin text-primary" />
        <span class="text-sm font-medium">Loading data...</span>
      </div>
    </div>

    <UForm>
      <!-- Fiat Configuration -->
      <UPageCard
        title="Fiat Configuration"
        description="Manage global currency settings."
        variant="subtle"
      >
        <div class="space-y-4">
          <div v-for="fiat in fiatStore.fiats" :key="fiat.id" class="flex items-center justify-between bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-full" :class="fiat.id === fiatStore.mainFiatId ? 'bg-primary-100 text-primary-600 dark:bg-primary-900/30' : 'bg-gray-100 text-gray-500 dark:bg-gray-800'">
                <UIcon :name="fiat.id === fiatStore.mainFiatId ? 'i-lucide-star' : 'i-lucide-coins'" class="w-5 h-5" />
              </div>
              <div>
                <div class="font-medium">
                  {{ fiat.name }}
                </div>
                <div class="text-xs text-gray-500">
                  {{ fiat.expression }}
                </div>
              </div>
            </div>

            <div class="flex items-center gap-4">
              <!-- Rate Editor (only for non-main) -->
              <div v-if="fiat.id !== fiatStore.mainFiatId && fiatStore.mainFiatId" class="flex items-center gap-2">
                <span class="text-sm text-gray-500">1 {{ fiatStore.fiats.find(f => f.id === fiatStore.mainFiatId)?.expression }} =</span>
                <UInput
                  v-model="fiatStore.exchangeRates[fiat.id]"
                  type="number"
                  placeholder="Rate"
                  class="w-24"
                  size="sm"
                  :loading="isSettingRate === fiat.id"
                  @blur="onSetRate(fiat.id)"
                />
                <span class="text-sm text-gray-500">{{ fiat.expression }}</span>
              </div>

              <UButton
                v-if="fiat.id !== fiatStore.mainFiatId"
                label="Set Main"
                variant="soft"
                size="xs"
                color="neutral"
                :loading="settingMainId === fiat.id"
                @click="onSetMainFiat(fiat.id)"
              />
              <UBadge
                v-else
                label="Main Currency"
                color="primary"
                variant="subtle"
              />

              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                size="xs"
                @click="openDeleteModal(fiat)"
              />
            </div>
          </div>

          <div v-if="fiatStore.fiats.length === 0" class="text-center text-gray-500 py-4">
            No currencies added yet.
          </div>
        </div>

        <USeparator class="my-6" />

        <h4 class="font-medium mb-2">
          Add New Currency
        </h4>
        <div class="flex gap-2 items-end">
          <UFormField label="Name" class="grow">
            <UInput v-model="newFiat.name" placeholder="Dollar" />
          </UFormField>
          <UFormField label="Expression" class="grow">
            <UInput v-model="newFiat.expression" placeholder="USD" />
          </UFormField>
          <UButton
            label="Add"
            :loading="isAddingFiat"
            color="primary"
            @click="onAddFiat"
          />
        </div>
      </UPageCard>

      <!-- Custom Comparisons -->
      <UPageCard
        title="Custom Comparisons"
        description="Define exchange rates between any two currencies."
        variant="subtle"
        class="mt-4"
      >
        <div class="space-y-3">
          <div
            v-for="comp in customComparisons"
            :key="comp.id"
            class="flex items-center justify-between bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700"
          >
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30">
                <UIcon name="i-lucide-arrow-left-right" class="w-4 h-4" />
              </div>
              <div>
                <div class="font-medium text-sm">
                  {{ getFiatName(comp.value_from) }}
                  <span class="text-gray-400 mx-1">→</span>
                  {{ getFiatName(comp.value_to) }}
                </div>
                <div class="text-xs text-gray-500">
                  {{ getFiatExpression(comp.value_from) }} → {{ getFiatExpression(comp.value_to) }}
                </div>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <span class="text-sm text-gray-500">1 {{ getFiatExpression(comp.value_from) }} =</span>
                <UInput
                  v-model="compRates[comp.id]"
                  type="number"
                  placeholder="Rate"
                  class="w-24"
                  size="sm"
                  :loading="updatingCompId === comp.id"
                  @blur="onUpdateCompRate(comp)"
                />
                <span class="text-sm text-gray-500">{{ getFiatExpression(comp.value_to) }}</span>
              </div>
              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                size="xs"
                @click="openDeleteCompModal(comp)"
              />
            </div>
          </div>

          <div v-if="customComparisons.length === 0" class="text-center text-gray-500 py-4">
            No custom comparisons yet.
          </div>
        </div>

        <USeparator class="my-6" />

        <h4 class="font-medium mb-2">
          Add Custom Comparison
        </h4>
        <div class="flex gap-2 items-end flex-wrap">
          <UFormField label="From Currency" class="grow">
            <USelect
              v-model="newComparison.fromId"
              :items="mainFiatOptions"
              value-key="value"
              placeholder="Select..."
            />
          </UFormField>
          <UFormField label="To Currency" class="grow">
            <USelect
              v-model="newComparison.toId"
              :items="mainFiatOptions"
              value-key="value"
              placeholder="Select..."
            />
          </UFormField>
          <UFormField label="Rate (1 From = X To)" class="grow">
            <UInput v-model="newComparison.rate" type="number" placeholder="Rate" />
          </UFormField>
          <UButton
            :loading="isAddingComparison"
            label="Add"
            color="primary"
            @click="onAddComparison"
          />
        </div>
      </UPageCard>

      <UModal v-model:open="deleteModalOpen" title="Delete Currency" description="Are you sure you want to delete this currency? This action cannot be undone.">
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton
              label="Cancel"
              color="neutral"
              variant="ghost"
              @click="deleteModalOpen = false"
            />
            <UButton
              label="Delete"
              color="error"
              :loading="isDeletingFiat"
              @click="confirmDelete"
            />
          </div>
        </template>
      </UModal>

      <UModal v-model:open="deleteCompModalOpen" title="Delete Comparison" description="Are you sure you want to delete this exchange rate comparison?">
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton
              label="Cancel"
              color="neutral"
              variant="ghost"
              @click="deleteCompModalOpen = false"
            />
            <UButton
              label="Delete"
              color="error"
              :loading="isDeletingComp"
              @click="confirmDeleteComp"
            />
          </div>
        </template>
      </UModal>
    </UForm>
  </div>
</template>
