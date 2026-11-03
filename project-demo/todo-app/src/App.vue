<script setup>
// ============================================
// App - 待办事项主组件 (Composition API)
// ============================================

import { ref, computed } from 'vue'
import { useTodos } from './composables/useTodos.js'
import TodoInput from './components/TodoInput.vue'
import TodoFilter from './components/TodoFilter.vue'
import TodoItem from './components/TodoItem.vue'

// 引入 todo 核心逻辑（含 localStorage 持久化）
const { todos, addTodo, toggleTodo, deleteTodo, clearCompleted, activeCount, completedCount, hasCompleted } = useTodos()

// 当前筛选模式
const filterType = ref('all')

/**
 * 根据当前筛选模式过滤待办事项
 */
const filteredTodos = computed(() => {
  if (filterType.value === 'active') {
    return todos.value.filter((t) => !t.completed)
  } else if (filterType.value === 'completed') {
    return todos.value.filter((t) => t.completed)
  }
  return todos.value
})

/**
 * 设置筛选模式
 */
function setFilter(type) {
  filterType.value = type
}

/**
 * 获取空状态的提示信息
 */
function getEmptyMessage() {
  switch (filterType.value) {
    case 'active':
      return '所有事项都已完成，太棒了！'
    case 'completed':
      return '还没有完成的事项'
    default:
      return '添加一个待办事项开始吧！'
  }
}
</script>

<template>
  <div class="min-h-screen py-8 px-4">
    <!-- 主容器 -->
    <div class="max-w-xl mx-auto">
      <!-- 标题区域 -->
      <header class="text-center mb-10">
        <h1 class="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
          待办事项
        </h1>
        <p class="text-gray-500 text-sm">高效管理你的每日任务</p>
      </header>

      <!-- 输入区域 -->
      <TodoInput @add="addTodo" />

      <!-- 筛选区域 -->
      <TodoFilter
        :filter-type="filterType"
        :counts="{ total: filteredTodos.length, activeCount: activeCount, completedCount: completedCount }"
        :on-filter-change="setFilter"
        @filter-change="setFilter"
      />

      <!-- 待办事项列表 -->
      <ul v-if="filteredTodos.length > 0" class="space-y-1">
        <TodoItem
          v-for="todo in filteredTodos"
          :key="todo.id"
          :todo="todo"
          @toggle="toggleTodo"
          @delete="deleteTodo"
        />
      </ul>

      <!-- 空状态提示 -->
      <div v-else class="text-center py-12">
        <div class="text-6xl mb-4">
          {{ filterType === 'completed' ? '🎉' : filterType === 'active' ? '🎊' : '📝' }}
        </div>
        <p class="text-gray-400 text-lg">
          {{ getEmptyMessage() }}
        </p>
      </div>

      <!-- 底部操作区 -->
      <footer
        v-if="hasCompleted"
        class="mt-6 flex justify-center"
      >
        <button
          @click="clearCompleted"
          class="px-5 py-2 text-sm text-gray-500 hover:text-red-500 bg-white rounded-full shadow-sm border border-gray-200 hover:border-red-200 hover:bg-red-50 transition-all duration-200"
        >
          清除已完成项 ({{ completedCount }})
        </button>
      </footer>
    </div>
  </div>
</template>
