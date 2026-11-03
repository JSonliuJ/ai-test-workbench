<script setup>
// ============================================
// TodoInput - 待办事项输入组件 (Composition API)
// 负责添加新事项
// ============================================

import { ref } from 'vue'

const emit = defineEmits(['add'])

// 输入框的响应式文本值
const inputText = ref('')

/**
 * 处理提交事件
 */
function handleSubmit() {
  if (inputText.value.trim()) {
    emit('add', inputText.value)
    inputText.value = '' // 清空输入框
  }
}

/**
 * 按下回车键时触发提交
 */
function handleKeydown(event) {
  if (event.key === 'Enter') {
    handleSubmit()
  }
}
</script>

<template>
  <!-- 输入框容器卡片 -->
  <div class="bg-white rounded-xl shadow-md p-1 mb-8">
    <form @submit.prevent="handleSubmit" class="flex gap-3">
      <!-- 文本输入框 -->
      <input
        v-model="inputText"
        type="text"
        placeholder="添加新的待办事项..."
        @keydown="handleKeydown"
        class="flex-1 px-5 py-3 bg-gray-50 border border-gray-200 rounded-lg text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200"
        autocomplete="off"
      />
      <!-- 添加按钮 -->
      <button
        type="submit"
        :disabled="!inputText.trim()"
        class="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-medium rounded-lg hover:from-blue-600 hover:to-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-sm hover:shadow-md"
      >
        添加
      </button>
    </form>
  </div>
</template>
