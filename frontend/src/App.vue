<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import axios from 'axios';

// --- 配置 ---
const API_BASE_URL = 'http://localhost:8000'; 

// --- 状态 ---
const tasks = ref([]);
const newTaskTitle = ref('');
const newTaskDescription = ref('');
const newTaskCategory = ref('');
const newTaskPriority = ref(2);
const newTaskDueDate = ref('');
const selectedCategory = ref(null);
const sortBy = ref(null);
const loading = ref(true);
const showCompleted = ref(false);
const visibleActiveCount = ref(10); // 懒加载：初始显示的待处理任务数量
const visibleCompletedCount = ref(10); // 懒加载：初始显示的已完成任务数量

// --- 分类选项 ---
const defaultCategories = ['工作', '学习', '生活', '其他'];

// 从任务中提取所有分类，合并默认分类
const categories = computed(() => {
  // 从现有任务中提取所有分类
  const taskCategories = [...new Set(tasks.value.map(task => task.category).filter(Boolean))];
  // 合并默认分类和任务分类，去重并排序
  return [...new Set([...defaultCategories, ...taskCategories])].sort();
});
const priorityOptions = [
  { value: 1, label: '高', icon: '🔥', color: '#ff4757' },
  { value: 2, label: '中', icon: '⚡', color: '#ffa502' },
  { value: 3, label: '低', icon: '💧', color: '#2ed573' }
];
const sortOptions = [
  { value: null, label: '创建时间', icon: '🕐' },
  { value: 'priority', label: '优先级', icon: '⭐' },
  { value: 'due_date', label: '截止日期', icon: '📅' }
];

// --- 计算属性 ---
const filteredTasks = computed(() => {
  let result = tasks.value;
  if (selectedCategory.value) {
    result = result.filter(task => task.category === selectedCategory.value);
  }
  return result;
});

// 监听筛选变化，重置懒加载计数
watch([selectedCategory, tasks], () => {
  visibleActiveCount.value = 10;
  visibleCompletedCount.value = 10;
});

const activeTasks = computed(() => filteredTasks.value.filter(task => !task.is_completed));
const completedTasks = computed(() => filteredTasks.value.filter(task => task.is_completed));

// 懒加载：只显示可见的任务
const visibleActiveTasks = computed(() => {
  return activeTasks.value.slice(0, visibleActiveCount.value);
});

const visibleCompletedTasks = computed(() => {
  return completedTasks.value.slice(0, visibleCompletedCount.value);
});

const hasMoreActiveTasks = computed(() => {
  return activeTasks.value.length > visibleActiveCount.value;
});

const hasMoreCompletedTasks = computed(() => {
  return completedTasks.value.length > visibleCompletedCount.value;
});

// --- API 方法 ---
const fetchTasks = async () => {
  loading.value = true;
  try {
    const params = {};
    if (sortBy.value) {
      params.sort_by = sortBy.value;
    }
    const response = await axios.get(`${API_BASE_URL}/tasks/`, { params });
    tasks.value = response.data;
    // 重置懒加载计数
    visibleActiveCount.value = 10;
    visibleCompletedCount.value = 10;
  } catch (error) {
    console.error("获取任务失败:", error);
    alert('无法连接到后端 API！请确保 Docker 服务已运行。');
  } finally {
    loading.value = false;
  }
};

const addTask = async () => {
  // 字符长度限制和验证
  const title = newTaskTitle.value.trim();
  if (!title) return;
  
  if (title.length > 255) {
    alert('任务标题不能超过255个字符！');
    return;
  }
  
  const description = newTaskDescription.value.trim() || null;
  if (description && description.length > 1000) {
    alert('任务描述不能超过1000个字符！');
    return;
  }
  
  const category = newTaskCategory.value.trim() || '其他';
  if (category.length > 50) {
    alert('分类名称不能超过50个字符！');
    return;
  }

  const taskData = {
    title: title,
    description: description,
    category: category,
    priority: newTaskPriority.value,
    due_date: newTaskDueDate.value || null
  };

  try {
    await axios.post(`${API_BASE_URL}/tasks/`, taskData);
    newTaskTitle.value = '';
    newTaskDescription.value = '';
    newTaskDueDate.value = '';
    newTaskCategory.value = ''; // 重置为空
    await fetchTasks();
  } catch (error) {
    console.error("添加任务失败:", error);
    if (error.response?.data?.detail) {
      alert(`添加任务失败：${error.response.data.detail}`);
    } else {
      alert('添加任务失败，请检查后端状态。');
    }
  }
};

const toggleCompletion = async (task) => {
  const newStatus = !task.is_completed;
  try {
    await axios.patch(`${API_BASE_URL}/tasks/${task.id}`, {
      is_completed: newStatus
    });
    task.is_completed = newStatus;
    await fetchTasks();
  } catch (error) {
    console.error("更新状态失败:", error);
    alert('更新状态失败。');
  }
};

const deleteTask = async (taskId) => {
  if (!confirm('确定要删除此任务吗？')) return;
  try {
    await axios.delete(`${API_BASE_URL}/tasks/${taskId}`);
    await fetchTasks();
  } catch (error) {
    console.error("删除失败:", error);
    alert('删除任务失败。');
  }
};

// --- 工具函数 ---
const isOverdue = (dateString) => {
  if (!dateString) return false;
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  return date < today;
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  const dateOnly = date.toISOString().split('T')[0];
  const todayOnly = today.toISOString().split('T')[0];
  const tomorrowOnly = tomorrow.toISOString().split('T')[0];
  
  if (dateOnly === todayOnly) {
    return '今天';
  } else if (dateOnly === tomorrowOnly) {
    return '明天';
  } else if (isOverdue(dateString)) {
    return `已过期 (${date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })})`;
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  }
};

const getPriorityInfo = (priority) => {
  return priorityOptions.find(opt => opt.value === (priority || 2)) || priorityOptions[1];
};

// --- 懒加载功能 ---
const loadMoreActiveTasks = () => {
  if (visibleActiveCount.value < activeTasks.value.length) {
    visibleActiveCount.value += 10;
  }
};

const loadMoreCompletedTasks = () => {
  if (visibleCompletedCount.value < completedTasks.value.length) {
    visibleCompletedCount.value += 10;
  }
};

// 使用 Intersection Observer 实现滚动懒加载
const setupLazyLoad = () => {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const trigger = entry.target;
        if (trigger.classList.contains('load-more-active')) {
          loadMoreActiveTasks();
        } else if (trigger.classList.contains('load-more-completed')) {
          loadMoreCompletedTasks();
        }
      }
    });
  }, {
    rootMargin: '100px' // 提前100px开始加载
  });

  // 观察所有加载更多触发器
  setTimeout(() => {
    const triggers = document.querySelectorAll('.load-more-trigger');
    triggers.forEach(trigger => {
      observer.observe(trigger);
    });
  }, 200);

  return observer;
};

// --- 生命周期 ---
onMounted(async () => {
  await fetchTasks();
  // 延迟设置懒加载，确保DOM已渲染
  setTimeout(() => {
    setupLazyLoad();
  }, 100);
});
</script>

<template>
  <div class="app-wrapper">
    <div class="background-animation"></div>
    
    <div class="container">
      <!-- 头部 -->
      <header class="header">
        <div class="header-content">
          <h1 class="title">
            <span class="title-icon">✨</span>
            <span class="title-text">我的待办</span>
          </h1>
          <div class="stats">
            <div class="stat-item">
              <span class="stat-number">{{ activeTasks.length }}</span>
              <span class="stat-label">待完成</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ completedTasks.length }}</span>
              <span class="stat-label">已完成</span>
            </div>
          </div>
        </div>
      </header>

      <!-- 主要内容区域：横屏时双栏布局 -->
      <div class="main-content">
        <!-- 左侧：表单和控制 -->
        <div class="left-panel">
          <!-- 添加任务表单 -->
          <div class="task-form-card">
        <div class="form-header">
          <span class="form-icon">➕</span>
          <span class="form-title">添加新任务</span>
        </div>
        
        <div class="form-body">
          <div class="input-row">
            <input 
              v-model="newTaskTitle" 
              @keyup.enter="addTask"
              placeholder="输入任务标题..." 
              class="task-input"
              maxlength="255"
            />
            <button @click="addTask" class="add-btn">
              <span class="btn-icon">✨</span>
              <span>添加</span>
            </button>
          </div>
          
          <div class="input-row">
            <textarea 
              v-model="newTaskDescription" 
              @keyup.ctrl.enter="addTask"
              placeholder="描述（可选）..." 
              class="task-textarea"
              rows="2"
              maxlength="1000"
            ></textarea>
          </div>
          
          <div class="input-row">
            <div class="category-input-wrapper">
              <input 
                v-model="newTaskCategory" 
                list="category-list"
                placeholder="选择或输入分类..." 
                class="form-select category-input"
                maxlength="50"
              />
              <datalist id="category-list">
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </datalist>
            </div>
            <select v-model="newTaskPriority" class="form-select">
              <option v-for="opt in priorityOptions" :key="opt.value" :value="opt.value">
                {{ opt.icon }} {{ opt.label }}
              </option>
            </select>
            <input 
              type="date" 
              v-model="newTaskDueDate" 
              class="form-select"
            />
          </div>
        </div>
      </div>

          <!-- 筛选和排序 -->
          <div class="controls-card">
            <div class="filter-section">
              <div class="filter-label">分类筛选</div>
              <div class="filter-buttons">
                <button 
                  @click="selectedCategory = null"
                  :class="['filter-btn', { active: selectedCategory === null }]"
                >
                  全部
                </button>
                <button 
                  v-for="cat in categories" 
                  :key="cat"
                  @click="selectedCategory = cat"
                  :class="['filter-btn', { active: selectedCategory === cat }]"
                >
                  {{ cat }}
                </button>
              </div>
            </div>
            
            <div class="sort-section">
              <div class="sort-label">排序方式</div>
              <select 
                v-model="sortBy" 
                @change="fetchTasks"
                class="sort-select"
              >
                <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
                  {{ opt.icon }} {{ opt.label }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- 右侧：任务列表 -->
        <div class="right-panel">
          <!-- 加载状态 -->
          <div v-if="loading" class="loading-card">
            <div class="spinner"></div>
            <span>加载中...</span>
          </div>

          <!-- 待处理任务 -->
          <section v-if="!loading && activeTasks.length" class="tasks-section">
            <div class="section-header">
              <h2 class="section-title">
                <span class="section-icon">📋</span>
                <span>待处理任务</span>
                <span class="badge">{{ activeTasks.length }}</span>
              </h2>
            </div>
            
            <transition-group name="task-list" tag="div" class="task-list">
              <div 
                v-for="(task, index) in visibleActiveTasks" 
                :key="task.id" 
                class="task-card"
                :style="{ animationDelay: `${index * 0.05}s` }"
              >
                <div class="task-checkbox-wrapper">
                  <input 
                    type="checkbox" 
                    :checked="task.is_completed" 
                    @change="toggleCompletion(task)"
                    class="task-checkbox"
                    :id="`task-${task.id}`"
                  />
                  <label :for="`task-${task.id}`" class="checkbox-label"></label>
                </div>
                
                <div class="task-content">
                  <div class="task-title">{{ task.title }}</div>
                  <div v-if="task.description" class="task-description">{{ task.description }}</div>
                  
                  <div class="task-tags">
                    <span class="tag category-tag">{{ task.category }}</span>
                    <span 
                      class="tag priority-tag" 
                      :style="{ backgroundColor: getPriorityInfo(task.priority || 2).color + '20', color: getPriorityInfo(task.priority || 2).color }"
                    >
                      {{ getPriorityInfo(task.priority || 2).icon }} {{ getPriorityInfo(task.priority || 2).label }}
                    </span>
                    <span 
                      v-if="task.due_date" 
                      class="tag date-tag"
                      :class="{ 'overdue': isOverdue(task.due_date) }"
                    >
                      📅 {{ formatDate(task.due_date) }}
                    </span>
                  </div>
                </div>
                
                <button 
                  class="delete-btn" 
                  @click="deleteTask(task.id)" 
                  title="删除任务"
                >
                  <span class="delete-icon">🗑️</span>
                </button>
              </div>
            </transition-group>
            
            <!-- 懒加载触发器 -->
            <div v-if="hasMoreActiveTasks" class="load-more-trigger load-more-active" @click="loadMoreActiveTasks">
              <button class="load-more-btn">
                <span>加载更多任务 ({{ activeTasks.length - visibleActiveCount }} 条剩余)</span>
                <span class="load-icon">⬇️</span>
              </button>
            </div>
          </section>

          <!-- 已完成任务 -->
          <section v-if="!loading && completedTasks.length" class="tasks-section completed-section">
            <div class="section-header">
              <button @click="showCompleted = !showCompleted" class="toggle-btn">
                <span class="section-icon">✅</span>
                <span>已完成任务</span>
                <span class="badge">{{ completedTasks.length }}</span>
                <span class="toggle-icon" :class="{ 'rotated': showCompleted }">▼</span>
              </button>
            </div>
            
            <transition name="slide">
              <div v-if="showCompleted" class="task-list">
                <div 
                  v-for="(task, index) in visibleCompletedTasks" 
                  :key="task.id" 
                  class="task-card completed"
                  :style="{ animationDelay: `${index * 0.05}s` }"
                >
                  <div class="task-checkbox-wrapper">
                    <input 
                      type="checkbox" 
                      :checked="task.is_completed" 
                      @change="toggleCompletion(task)"
                      class="task-checkbox"
                      :id="`completed-${task.id}`"
                    />
                    <label :for="`completed-${task.id}`" class="checkbox-label"></label>
                  </div>
                  
                  <div class="task-content">
                    <div class="task-title">{{ task.title }}</div>
                    <div v-if="task.description" class="task-description">{{ task.description }}</div>
                    
                    <div class="task-tags">
                      <span class="tag category-tag">{{ task.category }}</span>
                      <span 
                        class="tag priority-tag" 
                        :style="{ backgroundColor: getPriorityInfo(task.priority || 2).color + '20', color: getPriorityInfo(task.priority || 2).color }"
                      >
                        {{ getPriorityInfo(task.priority || 2).icon }} {{ getPriorityInfo(task.priority || 2).label }}
                      </span>
                    </div>
                  </div>
                  
                  <button 
                    class="delete-btn" 
                    @click="deleteTask(task.id)" 
                    title="删除任务"
                  >
                    <span class="delete-icon">🗑️</span>
                  </button>
                </div>
                
                <!-- 懒加载触发器 -->
                <div v-if="hasMoreCompletedTasks" class="load-more-trigger load-more-completed" @click="loadMoreCompletedTasks">
                  <button class="load-more-btn">
                    <span>加载更多任务 ({{ completedTasks.length - visibleCompletedCount }} 条剩余)</span>
                    <span class="load-icon">⬇️</span>
                  </button>
                </div>
              </div>
            </transition>
          </section>
      
          <!-- 空状态 -->
          <div v-if="!loading && tasks.length === 0" class="empty-state">
            <div class="empty-icon">🎉</div>
            <div class="empty-text">恭喜！目前没有待办事项</div>
            <div class="empty-subtext">添加你的第一个任务开始吧！</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.app-wrapper {
  min-height: 100vh;
  padding: 20px;
  position: relative;
  overflow-x: hidden;
}

.background-animation {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  z-index: -1;
  opacity: 0.1;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.left-panel,
.right-panel {
  width: 100%;
}

.header {
  margin-bottom: 30px;
  animation: fadeInDown 0.6s ease-out;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-icon {
  font-size: 2.5rem;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.stats {
  display: flex;
  gap: 15px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-5px) scale(1.05);
}

.stat-number {
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 0.85rem;
  color: #666;
  margin-top: 4px;
}

.task-form-card,
.controls-card,
.tasks-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.form-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
}

.form-icon {
  font-size: 1.2rem;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.task-input,
.task-textarea,
.form-select {
  flex: 1;
  min-width: 200px;
  padding: 14px 18px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: white;
}

.task-input:focus,
.task-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  transform: translateY(-2px);
}

.task-textarea {
  resize: vertical;
  min-height: 80px;
}

.category-input-wrapper {
  flex: 1;
  min-width: 200px;
  position: relative;
}

.category-input {
  width: 100%;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  white-space: nowrap;
}

.add-btn:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.add-btn:active {
  transform: translateY(0) scale(1);
}

.controls-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-section,
.sort-section {
  flex: 1;
  min-width: 200px;
}

.filter-label,
.sort-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 8px;
  font-weight: 600;
}

.filter-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 10px 20px;
  border: 2px solid #e0e0e0;
  background: white;
  color: #666;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-btn:hover {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
}

.filter-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.sort-select {
  width: 100%;
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 0.9rem;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sort-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.loading-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  gap: 20px;
  color: #666;
  font-size: 1.1rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.section-header {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
  color: #333;
}

.section-icon {
  font-size: 1.3rem;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 14px;
  font-size: 0.85rem;
  font-weight: 600;
  margin-left: 8px;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.3rem;
  font-weight: 600;
  color: #333;
  padding: 0;
}

.toggle-btn:hover {
  color: #667eea;
}

.toggle-icon {
  transition: transform 0.3s ease;
  font-size: 0.9rem;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 2px solid transparent;
  transition: all 0.3s ease;
  animation: slideInRight 0.5s ease-out backwards;
  position: relative;
  overflow: hidden;
}

.task-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transform: scaleY(0);
  transition: transform 0.3s ease;
}

.task-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: #667eea;
}

.task-card:hover::before {
  transform: scaleY(1);
}

.task-card.completed {
  opacity: 0.7;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.task-checkbox-wrapper {
  position: relative;
  flex-shrink: 0;
}

.task-checkbox {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-label {
  display: block;
  width: 24px;
  height: 24px;
  border: 2px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.checkbox-label::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(0);
  color: white;
  font-size: 16px;
  font-weight: bold;
  transition: transform 0.2s ease;
}

.task-checkbox:checked + .checkbox-label {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
}

.task-checkbox:checked + .checkbox-label::after {
  transform: translate(-50%, -50%) scale(1);
}

.task-checkbox:focus + .checkbox-label {
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2);
}

.task-content {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
  word-break: break-word;
}

.task-card.completed .task-title {
  text-decoration: line-through;
  color: #999;
}

.task-description {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 10px;
  line-height: 1.4;
  word-break: break-word;
}

.task-card.completed .task-description {
  text-decoration: line-through;
  color: #bbb;
}

.task-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

.category-tag {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.priority-tag {
  font-weight: 600;
}

.date-tag {
  background: rgba(0, 0, 0, 0.05);
  color: #666;
}

.date-tag.overdue {
  background: rgba(255, 71, 87, 0.1);
  color: #ff4757;
  font-weight: 600;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: rgba(255, 71, 87, 0.1);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
  opacity: 0.6;
}

.delete-btn:hover {
  background: rgba(255, 71, 87, 0.2);
  opacity: 1;
  transform: scale(1.1) rotate(90deg);
}

.delete-icon {
  font-size: 1.2rem;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  animation: fadeInUp 0.6s ease-out;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
  animation: bounce 2s infinite;
}

.empty-text {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.empty-subtext {
  font-size: 1rem;
  color: #666;
}

.task-list-enter-active,
.task-list-leave-active {
  transition: all 0.4s ease;
}

.task-list-enter-from {
  opacity: 0;
  transform: translateX(-30px) scale(0.9);
}

.task-list-leave-to {
  opacity: 0;
  transform: translateX(30px) scale(0.9);
}

.task-list-move {
  transition: transform 0.4s ease;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.4s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-20px);
}

.load-more-trigger {
  margin-top: 20px;
  text-align: center;
}

.load-more-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.load-more-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.load-icon {
  font-size: 1rem;
  animation: bounce 1s infinite;
}

/* 简单响应式 */
@media (max-width: 768px) {
  .app-wrapper {
    padding: 12px;
  }
  
  .container {
    padding: 0 12px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .input-row {
    flex-direction: column;
  }
  
  .task-input,
  .task-textarea,
  .form-select,
  .add-btn {
    width: 100%;
  }
  
  .controls-card {
    flex-direction: column;
  }
}
</style>
