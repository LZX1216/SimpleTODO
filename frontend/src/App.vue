<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

// --- 配置 ---
const API_BASE_URL = 'http://localhost:8000'; 

// --- 状态 ---
const tasks = ref([]);
const newTaskTitle = ref('');
const loading = ref(true);

// --- 计算属性：分类显示任务 ---
const activeTasks = computed(() => tasks.value.filter(task => !task.is_completed));
const completedTasks = computed(() => tasks.value.filter(task => task.is_completed));

// --- API 方法 ---

// 1. 获取任务列表 (READ)
const fetchTasks = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`${API_BASE_URL}/tasks/`);
    // 默认排序已经是后端处理的 created_at DESC
    tasks.value = response.data; 
  } catch (error) {
    console.error("获取任务失败:", error);
    alert('无法连接到后端 API！请确保 Docker 服务已运行。');
  } finally {
    loading.value = false;
  }
};

// 2. 添加任务 (CREATE)
const addTask = async () => {
  if (!newTaskTitle.value.trim()) return;

  const taskData = {
    title: newTaskTitle.value.trim(),
    description: "从前端添加的描述。",
    category: "Life" // 默认分类
  };

  try {
    await axios.post(`${API_BASE_URL}/tasks/`, taskData);
    newTaskTitle.value = ''; // 清空输入
    await fetchTasks(); // 刷新列表
  } catch (error) {
    console.error("添加任务失败:", error);
    alert('添加任务失败，请检查后端状态。');
  }
};

// 3. 标记完成 (UPDATE - PATCH)
const toggleCompletion = async (task) => {
  const newStatus = !task.is_completed;
  try {
    await axios.patch(`${API_BASE_URL}/tasks/${task.id}`, {
      is_completed: newStatus
    });
    // 乐观更新 UI
    task.is_completed = newStatus; 
    // 重新排序或刷新以确保已完成任务进入底部列表
    await fetchTasks();
  } catch (error) {
    console.error("更新状态失败:", error);
    alert('更新状态失败。');
  }
};

// 4. 删除任务 (DELETE)
const deleteTask = async (taskId) => {
  if (!confirm('确定要删除此任务吗？')) return;
  try {
    await axios.delete(`${API_BASE_URL}/tasks/${taskId}`);
    await fetchTasks(); // 刷新列表
  } catch (error) {
    console.error("删除失败:", error);
    alert('删除任务失败。');
  }
};

// --- 生命周期 ---
onMounted(fetchTasks);

</script>

<template>
  <div class="container">
    <h1>📝 Todo List (Python Backend)</h1>
    
    <div class="input-group">
      <input 
        v-model="newTaskTitle" 
        @keyup.enter="addTask"
        placeholder="输入新的待办事项标题..." 
      />
      <button @click="addTask">添加任务</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <section v-if="activeTasks.length" class="task-section">
      <h2>待处理 ({{ activeTasks.length }})</h2>
      <ul class="task-list">
        <li v-for="task in activeTasks" :key="task.id" class="task-item">
          <input 
            type="checkbox" 
            :checked="task.is_completed" 
            @change="toggleCompletion(task)"
          />
          <span class="task-title">{{ task.title }}</span>
          <span class="category">[{{ task.category }}]</span>
          <button class="delete-btn" @click="deleteTask(task.id)" title="删除任务">🗑️</button>
        </li>
      </ul>
    </section>

    <section v-if="completedTasks.length" class="task-section completed">
      <h2>已完成 ({{ completedTasks.length }})</h2>
      <ul class="task-list">
        <li v-for="task in completedTasks" :key="task.id" class="task-item completed">
          <input 
            type="checkbox" 
            :checked="task.is_completed" 
            @change="toggleCompletion(task)"
          />
          <span class="task-title">{{ task.title }}</span>
          <span class="category">[{{ task.category }}]</span>
          <button class="delete-btn" @click="deleteTask(task.id)" title="删除任务">🗑️</button>
        </li>
      </ul>
    </section>
    
    <p v-if="!loading && tasks.length === 0" class="empty-state">
      恭喜！目前没有待办事项。
    </p>

  </div>
</template>

<style>
/* 极简 CSS 样式 */
body {
  font-family: Arial, sans-serif;
  background-color: #f4f7f6;
  color: #333;
  margin: 0;
  padding: 20px;
}
.container {
  max-width: 600px;
  margin: 0 auto;
  background: #fff;
  padding: 30px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}
h1, h2 {
  color: #1e88e5;
  border-bottom: 2px solid #eee;
  padding-bottom: 10px;
  margin-top: 20px;
}
.input-group {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.input-group input {
  flex-grow: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.input-group button {
  padding: 10px 15px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.task-list {
  list-style: none;
  padding: 0;
}
.task-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed #eee;
  gap: 10px;
}
.task-item:last-child {
  border-bottom: none;
}
.task-item input[type="checkbox"] {
  margin-right: 5px;
  cursor: pointer;
  flex-shrink: 0;
}
.task-title {
  flex-grow: 1;
  word-break: break-word;
}
.task-item.completed .task-title {
  text-decoration: line-through;
  color: #999;
}
.category {
  font-size: 0.8em;
  color: #1e88e5;
  flex-shrink: 0;
}
.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2em;
  padding: 5px 8px;
  opacity: 0.6;
  transition: opacity 0.2s, transform 0.2s;
  flex-shrink: 0;
  border-radius: 4px;
}
.delete-btn:hover {
  opacity: 1;
  transform: scale(1.1);
  background-color: #ffebee;
}
.delete-btn:active {
  transform: scale(0.95);
}
.loading, .empty-state {
  text-align: center;
  color: #f57c00;
  padding: 20px;
}
</style>