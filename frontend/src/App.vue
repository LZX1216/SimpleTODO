<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import axios from 'axios';

// --- 配置 ---
const API_BASE_URL = 'http://localhost:8000'; 

// --- 状态 ---
const tasks = ref([]);
const newTaskTitle = ref('');
const newTaskDescription = ref('');
const newTaskCategory = ref('生活');
const newTaskPriority = ref(2);
const newTaskDueDate = ref('');
const selectedCategory = ref(null);
const sortBy = ref(null);
const loading = ref(true);
const showCompleted = ref(false);
const visibleActiveCount = ref(10); // 懒加载：初始显示的待处理任务数量
const visibleCompletedCount = ref(10); // 懒加载：初始显示的已完成任务数量

// --- 分类选项 ---
const categories = ['工作', '学习', '生活', '其他'];
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
  if (!newTaskTitle.value.trim()) return;

  const taskData = {
    title: newTaskTitle.value.trim(),
    description: newTaskDescription.value.trim() || null,
    category: newTaskCategory.value,
    priority: newTaskPriority.value,
    due_date: newTaskDueDate.value || null
  };

  try {
    await axios.post(`${API_BASE_URL}/tasks/`, taskData);
    newTaskTitle.value = '';
    newTaskDescription.value = '';
    newTaskDueDate.value = '';
    await fetchTasks();
  } catch (error) {
    console.error("添加任务失败:", error);
    alert('添加任务失败，请检查后端状态。');
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
            ></textarea>
          </div>
          
          <div class="input-row">
            <select v-model="newTaskCategory" class="form-select">
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
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
  background: #f5f5f5;
}

.background-animation {
  display: none;
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
  font-size: 2rem;
  font-weight: 700;
  color: #333;
}

.title-icon {
  font-size: 2rem;
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
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  font-size: 0.85rem;
  color: #666;
  margin-top: 4px;
}

.task-form-card,
.controls-card,
.tasks-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.task-input:focus,
.task-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
}

.task-textarea {
  resize: vertical;
  min-height: 80px;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.add-btn:hover {
  background: #5568d3;
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
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  color: #666;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
}

.filter-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.filter-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.sort-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
}

.sort-select:focus {
  outline: none;
  border-color: #667eea;
}

.loading-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  gap: 20px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
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
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  background: #667eea;
  color: white;
  border-radius: 12px;
  font-size: 0.8rem;
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
  gap: 12px;
}

.task-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
}

.task-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.task-card.completed {
  opacity: 0.6;
}

.task-checkbox-wrapper {
  flex-shrink: 0;
}

.task-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
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
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  white-space: nowrap;
}

.category-tag {
  background: #e8ecff;
  color: #667eea;
}

.priority-tag {
  font-weight: 600;
}

.date-tag {
  background: #f0f0f0;
  color: #666;
}

.date-tag.overdue {
  background: #ffe8e8;
  color: #ff4757;
  font-weight: 600;
}

.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #ffe8e8;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  flex-shrink: 0;
}

.delete-btn:hover {
  background: #ffd0d0;
}

.delete-icon {
  font-size: 1rem;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.empty-subtext {
  font-size: 0.9rem;
  color: #666;
}

.task-list-enter-active,
.task-list-leave-active {
  transition: opacity 0.3s ease;
}

.task-list-enter-from,
.task-list-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
}

.load-more-trigger {
  margin-top: 20px;
  text-align: center;
}

.load-more-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

.load-more-btn:hover {
  background: #5568d3;
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
