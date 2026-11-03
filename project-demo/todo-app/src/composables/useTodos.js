// ============================================
// Todo Composable - 待办事项核心逻辑
// 包含增删改查、localStorage 数据持久化
// ============================================

import { ref, computed } from 'vue'

/**
 * 模块级最大 ID，初始值基于当前时间和已保存数据中的最大 ID 取较大者，
 * 避免多标签页同时打开时产生 ID 冲突（两标签页各自独立初始化，若仅用 Date.now()
 * 可能得到相同的起始值，跨标签页合并时会出现重复 key）。
 */
let uniqueId = Date.now()

// 在初始化后，如果有已保存的数据，确保 uniqueId 不小于已有数据的最大 ID
export function syncUniqueId(savedData) {
  if (savedData && Array.isArray(savedData)) {
    const maxExisting = savedData.reduce(
      (max, item) => Math.max(max, Number(item.id) || 0),
      0
    )
    if (maxExisting > uniqueId) {
      uniqueId = maxExisting
    }
  }
}

// 安全地读写 localStorage，防止 CSP 等环境限制导致崩溃
const storage = {
  getItem(key) {
    try { return localStorage.getItem(key) } catch (e) { return null }
  },
  setItem(key, value) {
    try { localStorage.setItem(key, value) } catch (e) { /* 忽略写入失败 */ }
  },
}

/**
 * 创建 Todo 数据响应式引用
 * @returns {Object} 包含所有 todo 状态和方法的响应式对象
 */
export function useTodos() {
  // 从 localStorage 读取已保存的待办事项，没有则为空数组
  const savedData = storage.getItem('todo-app-data')
  let parsedData = []
  try {
    parsedData = JSON.parse(savedData || '[]')
  } catch (e) {
    parsedData = []
  }

  // 确保 uniqueId 不小于已有数据的最大 ID，避免跨标签页 ID 冲突
  syncUniqueId(parsedData)

  const todos = ref(parsedData)

  /**
   * 获取下一个唯一 ID（基于时间戳递增）
   * @returns {number} 唯一 ID
   */
  function getNextId() {
    return ++uniqueId
  }

  /**
   * 将 todos 保存到 localStorage
   */
  function saveToLocalStorage() {
    storage.setItem('todo-app-data', JSON.stringify(todos.value))
  }

  /**
   * 添加新的待办事项
   * @param {string} text - 待办事项的文本内容
   */
  function addTodo(text) {
    if (!text.trim()) return // 空文本不处理
    todos.value.push({
      id: getNextId(),
      text: text.trim(),
      completed: false,
      createdAt: new Date().toISOString(),
    })
    saveToLocalStorage()
  }

  /**
   * 切换待办事项的完成状态
   * @param {number} id - 待办事项的唯一 ID
   */
  function toggleTodo(id) {
    const todo = todos.value.find((item) => item.id === id)
    if (todo) {
      todo.completed = !todo.completed
      saveToLocalStorage()
    }
  }

  /**
   * 删除指定的待办事项
   * @param {number} id - 待办事项的唯一 ID
   */
  function deleteTodo(id) {
    todos.value = todos.value.filter((item) => item.id !== id)
    saveToLocalStorage()
  }

  /**
   * 清除所有已完成的事项
   */
  function clearCompleted() {
    todos.value = todos.value.filter((item) => !item.completed)
    saveToLocalStorage()
  }

  // ==================== 计算属性 ====================

  /**
   * 未完成的事项数量
   */
  const activeCount = computed(() => todos.value.filter((t) => !t.completed).length)

  /**
   * 已完成的事项数量
   */
  const completedCount = computed(() => todos.value.filter((t) => t.completed).length)

  /**
   * 是否有可清除的已完成事项
   */
  const hasCompleted = computed(() => todos.value.some((t) => t.completed))

  return {
    todos, // 待办事项列表（响应式）
    addTodo, // 添加待办事项
    toggleTodo, // 切换完成状态
    deleteTodo, // 删除待办事项
    clearCompleted, // 清除已完成事项
    activeCount, // 未完成数量
    completedCount, // 已完成数量
    hasCompleted, // 是否有已完成项
  }
}
