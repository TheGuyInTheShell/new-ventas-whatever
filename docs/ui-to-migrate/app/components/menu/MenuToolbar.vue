<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  search: string
  sortBy: string
}>()

const emit = defineEmits(['update:search', 'update:sortBy'])

const localSearch = ref(props.search)
const localSortBy = ref(props.sortBy)

watch(() => props.search, (val) => {
  localSearch.value = val
})

watch(() => props.sortBy, (val) => {
  localSortBy.value = val
})

watch(localSearch, (val) => {
  emit('update:search', val)
})

watch(localSortBy, (val) => {
  emit('update:sortBy', val)
})

const sortOptions = [
  { label: 'Alphabetical', value: 'name_asc' },
  { label: 'Price: Low to High', value: 'price_asc' },
  { label: 'Price: High to Low', value: 'price_desc' }
]
</script>

<template>
  <div class="flex flex-col sm:flex-row gap-4 mb-4">
    <UInput
      v-model="localSearch"
      icon="i-lucide-search"
      placeholder="Search dishes..."
      class="flex-1"
      size="lg"
    />
    <USelect
      v-model="localSortBy"
      :items="sortOptions"
      :options="sortOptions"
      size="lg"
      class="w-full sm:w-48"
    />
  </div>
</template>
