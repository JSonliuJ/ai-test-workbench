// 应用入口文件
import { createApp } from 'vue'
import App from './App.vue'
import './style.css' // 引入 Tailwind CSS 样式

try {
  const app = createApp(App)
  app.mount('#app')
  console.log('✅ Vue 应用已成功挂载')
} catch (error) {
  console.error('❌ Vue 应用挂载失败:', error)
  document.getElementById('app').innerHTML = '<div style="padding:20px;color:red;"><h3>应用加载出错</h3><p>' + error.message + '</p></div>'
}
