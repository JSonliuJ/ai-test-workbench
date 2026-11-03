<script setup>
// ============================================
// TodoItem - 待办事项单项组件 (Composition API)
// 支持标记完成/删除操作
// ============================================

const props = defineProps({
  todo: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['toggle', 'delete'])

/**
 * 切换完成状态
 */
function handleToggle() {
  emit('toggle', props.todo.id)
}

/**
 * 删除事项
 */
function handleDelete() {
  emit('delete', props.todo.id)
}
</script>

<template>
  <li
    class="group flex items-center gap-3 bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-2 hover:shadow-md transition-all duration-200 transform hover:translate-x-1"
  >
    <!-- 复选框 -->
    <button
      @click="handleToggle"
      :class="[
        'w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-200 flex-shrink-0',
        todo.completed
          ? 'bg-gradient-to-r from-blue-500 to-indigo-500 border-transparent'
          : 'border-gray-300 hover:border-blue-400',
      ]"
      :aria-label="todo.completed ? '标记为未完成' : '标记为已完成'"
    >
      <!-- 勾选图标 -->
      <svg
        v-if="todo.completed"
        class="w-4 h-4 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="3"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    </button>

    <!-- 事项文本（带删除线效果） -->
    <span
      :class="[
        'flex-1 text-base transition-all duration-200 cursor-pointer select-none',
        todo.completed ? 'line-through text-gray-400' : 'text-gray-700',
      ]"
      @click="handleToggle"
    >
      {{ todo.text }}
    </span>

    <!-- 删除按钮 -->
    <button
      @click="handleDelete"
      class="opacity-0 group-hover:opacity-100 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all duration-200"
      :aria-label="`删除: ${todo.text}`"
    >
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M9 17h6" />
      </svg>
    </button>
  </li>
</template>
