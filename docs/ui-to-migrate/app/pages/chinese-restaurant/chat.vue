<script setup lang="ts">
</script>

<template>
  <div class="p-4 h-full flex flex-col w-full">
    <h1 class="text-2xl font-bold mb-4">
      AI Assistant Chat
    </h1>
    <div class="grow border rounded-lg p-4 bg-gray-50 dark:bg-gray-900 overflow-y-auto mb-4">
      <div class="text-center text-gray-500 mt-20">
        <UIcon name="i-lucide-bot" class="w-16 h-16 mb-2" />
        <p>Chat interface to generate dynamic graphs will be implemented here.</p>
      </div>
    </div>
    <div class="flex gap-2">
      <UInput placeholder="Ask about sales, expenses..." class="grow" />
      <UButton icon="i-lucide-send" label="Send" />
    </div>
  </div>
</template>
