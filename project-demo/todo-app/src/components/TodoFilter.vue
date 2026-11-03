<script setup>
// ============================================
// TodoFilter - 待办事项筛选组件 (Composition API)
// 支持全部/未完成/已完成三种筛选模式
// ============================================

const props = defineProps({
  filterType: {
    type: String,
    default: 'all', // all | active | completed
  },
  counts: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['filter-change'])

/**
 * 筛选选项配置
 */
const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '未完成', value: 'active' },
  { label: '已完成', value: 'completed' },
]

/**
 * 处理筛选变更
 */
function handleFilterChange(value) {
  if (value !== props.filterType) {
    emit('filter-change', value)
  }
}
</script>

<template>
  <!-- 筛选按钮组 -->
  <div class="flex items-center gap-2 justify-center mb-6">
    <button
      v-for="option in filterOptions"
      :key="option.value"
      @click="handleFilterChange(option.value)"
      :class="[
        'px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
        filterType === option.value
          ? 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-sm'
          : 'text-gray-500 hover:bg-white hover:shadow-sm',
      ]"
    >
      {{ option.label }}
      <span :class="filterType === option.value ? 'ml-1' : ''">
        {{ option.value !== 'all' ? counts[`${option.value}Count`] || 0 : counts.total }}
      </span>
    </button>
  </div>
</template>
