<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import axios from 'axios';

// --- 配置 ---
const API_BASE_URL = 'http://localhost:8000'; 

// --- 状态 ---
const tasks = ref([]); // 筛选后的任务列表（用于显示）
const allTasks = ref([]); // 所有任务列表（用于统计和分类显示，不受筛选影响）
const newTaskTitle = ref('');
const newTaskDescription = ref('');
const newTaskCategory = ref('');
const newTaskPriority = ref(2);
const newTaskDueDate = ref('');
const selectedCategory = ref(null);
const selectedDateFilter = ref(null); // 日期筛选：overdue, today, tomorrow, this_week, this_month, no_due_date
const sortBy = ref('due_date'); // 默认按到期时间排序
const searchKeyword = ref(''); // 搜索关键词
const showScrollToTop = ref(false); // 是否显示回到顶部按钮
const loading = ref(true);
const showCompleted = ref(false);
const showActiveTasks = ref(true); // 待处理任务是否展开（默认展开）
const visibleActiveCount = ref(10); // 懒加载：初始显示的待处理任务数量
const visibleCompletedCount = ref(10); // 懒加载：初始显示的已完成任务数量
const editingTaskId = ref(null); // 正在编辑的任务ID
let lazyLoadObserver = null; // 懒加载观察器引用
const showAddTask = ref(false); // 窄屏幕下是否显示添加任务表单
const showSearch = ref(false); // 窄屏幕下是否显示搜索和筛选
const showStats = ref(false); // 窄屏幕下是否显示任务统计
const expandedDescriptions = ref(new Set()); // 展开描述的任务ID集合

// 互斥切换函数
const toggleSection = (section) => {
  // 检查当前点击的section是否已经打开
  let isCurrentlyOpen = false;
  if (section === 'addTask' && showAddTask.value) {
    isCurrentlyOpen = true;
  } else if (section === 'search' && showSearch.value) {
    isCurrentlyOpen = true;
  } else if (section === 'stats' && showStats.value) {
    isCurrentlyOpen = true;
  }
  
  // 先关闭所有
  showAddTask.value = false;
  showSearch.value = false;
  showStats.value = false;
  
  // 如果当前点击的section已经打开，则关闭（不打开）；否则打开对应的section
  if (!isCurrentlyOpen) {
    if (section === 'addTask') {
      showAddTask.value = true;
    } else if (section === 'search') {
      showSearch.value = true;
    } else if (section === 'stats') {
      showStats.value = true;
    }
  }
};
const editForm = ref({
  title: '',
  description: '',
  category: '',
  priority: 2,
  due_date: ''
});

// 打开日期选择器
const openDatePicker = (type, taskId = null) => {
  if (type === 'new') {
    // 触发原生日期选择器
    setTimeout(() => {
      const input = document.getElementById('new-task-date-input');
      if (input) {
        input.focus();
        input.showPicker?.();
      }
    }, 10);
  } else if (type === 'edit') {
    setTimeout(() => {
      // 尝试两个可能的ID（待处理任务和已完成任务）
      const input = document.getElementById(`edit-task-date-input-${taskId}`) || 
                    document.getElementById(`edit-completed-task-date-input-${taskId}`);
      if (input) {
        input.focus();
        input.showPicker?.();
      }
    }, 10);
  }
};

// --- 分类选项 ---
const defaultCategories = ['工作', '学习', '生活', '其他'];
const defaultCategoriesWithoutOther = ['工作', '学习', '生活']; // 默认分类（不含"其他"）

// 从所有任务中提取所有分类，合并默认分类（不受筛选影响）
const categories = computed(() => {
  // 从所有任务中提取所有分类（使用 allTasks 而不是 tasks）
  const taskCategories = [...new Set(allTasks.value.map(task => task.category).filter(Boolean))];
  
  // 合并所有分类并去重
  const allCategories = [...new Set([...defaultCategories, ...taskCategories])];
  
  // 分离默认分类（不含"其他"）、自定义分类和"其他"
  // 保持默认分类的指定顺序
  const defaultCats = defaultCategoriesWithoutOther.filter(cat => allCategories.includes(cat));
  const customCats = allCategories.filter(cat => 
    !defaultCategories.includes(cat)
  ).sort(); // 自定义分类按字母顺序排序
  const otherCat = allCategories.filter(cat => cat === '其他');
  
  // 组合：默认分类（不含"其他"） -> 自定义分类 -> "其他"
  return [...defaultCats, ...customCats, ...otherCat];
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
// 注意：分类筛选现在在后端完成，这里保留 filteredTasks 以保持代码兼容性
const filteredTasks = computed(() => {
  // 由于分类筛选已在后端完成，直接返回 tasks
  return tasks.value;
});

// 监听筛选变化，重置懒加载计数（不监听tasks，避免编辑后重置）
watch([selectedCategory, selectedDateFilter, searchKeyword], () => {
  visibleActiveCount.value = 10;
  visibleCompletedCount.value = 10;
});

// 用于显示的任务（筛选后）
const activeTasks = computed(() => filteredTasks.value.filter(task => !task.is_completed));
const completedTasks = computed(() => filteredTasks.value.filter(task => task.is_completed));

// 用于统计的任务（所有任务，不受筛选影响）
const allActiveTasks = computed(() => allTasks.value.filter(task => !task.is_completed));
const allCompletedTasks = computed(() => allTasks.value.filter(task => task.is_completed));

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

// --- 工具函数（需要在统计计算之前定义）---
const isOverdue = (dateString) => {
  if (!dateString) return false;
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  return date < today;
};

// 计算日期差（天数）
const getDaysDifference = (dateString) => {
  if (!dateString) return 0;
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  const diffTime = date - today;
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};

// --- 统计计算属性 ---
// 完成率（基于所有任务）
const completionRate = computed(() => {
  const total = allTasks.value.length;
  if (total === 0) return 0;
  return Math.round((allCompletedTasks.value.length / total) * 100);
});

// 按分类统计（基于所有任务）
const categoryStats = computed(() => {
  const stats = {};
  allTasks.value.forEach(task => {
    const cat = task.category || '其他';
    if (!stats[cat]) {
      stats[cat] = { total: 0, completed: 0 };
    }
    stats[cat].total++;
    if (task.is_completed) {
      stats[cat].completed++;
    }
  });
  return Object.entries(stats).map(([category, data]) => ({
    category,
    total: data.total,
    completed: data.completed,
    rate: data.total > 0 ? Math.round((data.completed / data.total) * 100) : 0
  })).sort((a, b) => b.total - a.total);
});

// 按优先级统计（基于所有任务）
const priorityStats = computed(() => {
  const stats = {
    high: { total: 0, completed: 0, label: '高', icon: '🔥', color: '#ff4757' },
    medium: { total: 0, completed: 0, label: '中', icon: '⚡', color: '#ffa502' },
    low: { total: 0, completed: 0, label: '低', icon: '💧', color: '#2ed573' }
  };
  
  allTasks.value.forEach(task => {
    const priority = task.priority || 2;
    let key = 'medium';
    if (priority === 1) key = 'high';
    else if (priority === 3) key = 'low';
    
    stats[key].total++;
    if (task.is_completed) {
      stats[key].completed++;
    }
  });
  
  return Object.values(stats).map(stat => ({
    ...stat,
    rate: stat.total > 0 ? Math.round((stat.completed / stat.total) * 100) : 0
  }));
});

// 过期任务统计（基于所有任务）
const overdueTasks = computed(() => {
  return allActiveTasks.value.filter(task => {
    if (!task.due_date) return false;
    return isOverdue(task.due_date);
  });
});

// --- API 方法 ---
const fetchTasks = async () => {
  loading.value = true;
  try {
    // 先获取所有任务（用于统计和分类显示）
    const allTasksResponse = await axios.get(`${API_BASE_URL}/tasks/`, {});
    allTasks.value = allTasksResponse.data;
    
    // 然后获取筛选后的任务（用于显示）
    const params = {};
    if (sortBy.value) {
      params.sort_by = sortBy.value;
    }
    if (searchKeyword.value && searchKeyword.value.trim()) {
      params.search = searchKeyword.value.trim();
    }
    // 如果选择了分类，也传递给后端（与搜索可以同时使用）
    if (selectedCategory.value) {
      params.category = selectedCategory.value;
    }
    // 如果选择了日期筛选，也传递给后端
    if (selectedDateFilter.value) {
      params.date_filter = selectedDateFilter.value;
    }
    const response = await axios.get(`${API_BASE_URL}/tasks/`, { params });
    tasks.value = response.data;
    // 只有在筛选条件变化时才重置懒加载计数，否则保持当前显示数量
    // 这样编辑任务后不会重置为10条
    // 注意：watch 中已经处理了筛选变化时的重置
  } catch (error) {
    console.error("获取任务失败:", error);
    alert('无法连接到后端 API！请确保 Docker 服务已运行。');
  } finally {
    loading.value = false;
  }
};

// 搜索防抖处理
let searchTimeout = null;
const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  searchTimeout = setTimeout(() => {
    fetchTasks();
  }, 300); // 300ms 防抖延迟
};

// 清除搜索
const clearSearch = () => {
  searchKeyword.value = '';
  fetchTasks();
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

// --- 编辑功能 ---
const startEdit = (task) => {
  editingTaskId.value = task.id;
  editForm.value = {
    title: task.title,
    description: task.description || '',
    category: task.category || '其他',
    priority: task.priority || 2,
    due_date: task.due_date || ''
  };
};

const cancelEdit = () => {
  editingTaskId.value = null;
  editForm.value = {
    title: '',
    description: '',
    category: '',
    priority: 2,
    due_date: ''
  };
};

const saveEdit = async (taskId) => {
  // 字符长度限制和验证
  const title = editForm.value.title.trim();
  if (!title) {
    alert('任务标题不能为空！');
    return;
  }
  
  if (title.length > 255) {
    alert('任务标题不能超过255个字符！');
    return;
  }
  
  const description = editForm.value.description.trim() || null;
  if (description && description.length > 1000) {
    alert('任务描述不能超过1000个字符！');
    return;
  }
  
  const category = editForm.value.category.trim() || '其他';
  if (category.length > 50) {
    alert('分类名称不能超过50个字符！');
    return;
  }

  const taskData = {
    title: title,
    description: description,
    category: category,
    priority: editForm.value.priority,
    due_date: editForm.value.due_date || null
  };

  try {
    await axios.patch(`${API_BASE_URL}/tasks/${taskId}`, taskData);
    editingTaskId.value = null;
    await fetchTasks();
    // 保存后重新设置懒加载观察器，确保懒加载继续工作
    setTimeout(() => {
      setupLazyLoad();
    }, 200);
  } catch (error) {
    console.error("更新任务失败:", error);
    if (error.response?.data?.detail) {
      alert(`更新任务失败：${error.response.data.detail}`);
    } else {
      alert('更新任务失败，请检查后端状态。');
    }
  }
};

// --- 导出功能 ---
const exportTasks = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tasks/export`);
    const exportData = response.data;
    
    // 导出为 JSON 文件
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `tasks_export_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    alert(`任务数据已导出为 JSON 文件！共 ${exportData.total_tasks} 条任务。`);
  } catch (error) {
    console.error("导出失败:", error);
    alert('导出任务失败，请检查后端状态。');
  }
};

// --- 导入功能 ---
const importTasks = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  // 验证文件类型
  if (!file.name.endsWith('.json')) {
    alert('请选择 JSON 格式的文件！');
    event.target.value = ''; // 清空文件选择
    return;
  }
  
  try {
    // 读取文件内容
    const fileContent = await file.text();
    const importData = JSON.parse(fileContent);
    
    // 验证数据格式
    if (!importData.tasks || !Array.isArray(importData.tasks)) {
      alert('JSON 文件格式错误！应包含 "tasks" 数组字段。');
      event.target.value = '';
      return;
    }
    
    if (importData.tasks.length === 0) {
      alert('任务列表为空，无法导入！');
      event.target.value = '';
      return;
    }
    
    // 确认导入
    const confirmMsg = `确定要导入 ${importData.tasks.length} 条任务吗？\n\n注意：导入的任务会添加到现有任务中，不会覆盖现有数据。`;
    if (!confirm(confirmMsg)) {
      event.target.value = '';
      return;
    }
    
    // 发送导入请求
    const response = await axios.post(`${API_BASE_URL}/tasks/import`, importData);
    
    // 导入成功，刷新任务列表
    await fetchTasks();
    alert(`成功导入 ${response.data.length} 条任务！`);
    
  } catch (error) {
    console.error("导入失败:", error);
    if (error.response?.data?.detail) {
      alert(`导入失败：${error.response.data.detail}`);
    } else if (error instanceof SyntaxError) {
      alert('JSON 文件格式错误，请检查文件内容！');
    } else {
      alert('导入任务失败，请检查后端状态。');
    }
  } finally {
    // 清空文件选择，允许重复选择同一文件
    event.target.value = '';
  }
};

// 触发文件选择
const triggerImport = () => {
  const fileInput = document.getElementById('import-file-input');
  if (fileInput) {
    fileInput.click();
  }
};

// --- 工具函数 ---
const formatDate = (dateString) => {
  if (!dateString) return '';
  
  // 处理日期字符串，支持多种格式
  let date;
  if (typeof dateString === 'string') {
    // 处理可能的日期格式：YYYY-MM-DD, YYYY/MM/DD, YYYY-MM-DDTHH:mm:ss 等
    let datePart = dateString.split('T')[0]; // 处理可能包含时间的字符串
    datePart = datePart.split(' ')[0]; // 处理可能包含空格的情况
    
    // 如果包含斜杠，转换为短横线
    if (datePart.includes('/')) {
      datePart = datePart.replace(/\//g, '-');
    }
    
    // 尝试解析日期
    date = new Date(datePart + 'T00:00:00');
    
    // 如果解析失败，尝试其他方式
    if (isNaN(date.getTime())) {
      date = new Date(datePart);
    }
  } else {
    date = new Date(dateString);
  }
  
  // 检查日期是否有效
  if (isNaN(date.getTime())) {
    console.warn('无法解析日期:', dateString);
    return dateString; // 如果日期无效，返回原始字符串
  }
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  // 使用本地日期进行比较，避免时区问题
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const tomorrowOnly = new Date(tomorrow.getFullYear(), tomorrow.getMonth(), tomorrow.getDate());
  
  // 计算日期差
  const daysDiff = getDaysDifference(dateString);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const year = date.getFullYear();
  const currentYear = new Date().getFullYear();
  
  // 如果日期不在今年，则加上年份
  let formattedDate;
  if (year !== currentYear) {
    formattedDate = `${year}年${month}月${day}日`;
  } else {
    formattedDate = `${month}月${day}日`;
  }
  
  if (dateOnly.getTime() === todayOnly.getTime()) {
    return `今天（${formattedDate}）`;
  } else if (dateOnly.getTime() === tomorrowOnly.getTime()) {
    return `明天（${formattedDate}）`;
  } else if (daysDiff < 0) {
    // 已过期
    const daysOverdue = Math.abs(daysDiff);
    return `已过期${daysOverdue}天（${formattedDate}）`;
  } else {
    // 未来日期
    return `${daysDiff}天后（${formattedDate}）`;
  }
};

const getPriorityInfo = (priority) => {
  return priorityOptions.find(opt => opt.value === (priority || 2)) || priorityOptions[1];
};

// 切换描述展开/收起
const toggleDescription = (taskId) => {
  if (expandedDescriptions.value.has(taskId)) {
    expandedDescriptions.value.delete(taskId);
  } else {
    expandedDescriptions.value.add(taskId);
  }
};

// 检查描述是否需要展开/收起按钮（超过一定长度）
const shouldShowExpandButton = (description) => {
  if (!description) return false;
  // 如果描述超过100个字符或者包含换行符，显示展开/收起按钮
  return description.length > 100 || description.includes('\n');
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
  // 如果已有观察器，先断开
  if (lazyLoadObserver) {
    lazyLoadObserver.disconnect();
  }
  
  lazyLoadObserver = new IntersectionObserver((entries) => {
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
      lazyLoadObserver.observe(trigger);
    });
  }, 200);
};

// 滚动到顶部
const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
};

// 监听滚动，显示/隐藏回到顶部按钮
const handleScroll = () => {
  showScrollToTop.value = window.scrollY > 300;
};

// --- 生命周期 ---
onMounted(async () => {
  await fetchTasks();
  // 延迟设置懒加载，确保DOM已渲染
  setTimeout(() => {
    setupLazyLoad();
  }, 100);
  // 监听滚动事件
  window.addEventListener('scroll', handleScroll);
});

// 组件卸载时移除滚动监听
onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<template>
  <div class="app-wrapper">
    <div class="background-animation"></div>
    
    <div class="container">
            <header class="header">
        <div class="header-content">
          <h1 class="title">
            <span class="title-icon">📝</span>
            <span class="title-text">我的待办</span>
          </h1>
          <div class="header-actions">
            <div class="stats">
              <div class="stat-item">
                <span class="stat-number">{{ allActiveTasks.length }}</span>
                <span class="stat-label">待完成</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ allCompletedTasks.length }}</span>
                <span class="stat-label">已完成</span>
              </div>
              <div class="stat-item" v-if="overdueTasks.length > 0">
                <span class="stat-number stat-number-overdue">{{ overdueTasks.length }}</span>
                <span class="stat-label">已过期</span>
              </div>
            </div>
            <div class="export-buttons">
              <input 
                type="file" 
                id="import-file-input"
                accept=".json"
                @change="importTasks"
                style="display: none;"
              />
              <button class="export-btn" @click="triggerImport" title="导入 JSON 文件">
                <span class="export-icon">📤</span>
                <span class="export-text">导入 JSON</span>
              </button>
              <button class="export-btn" @click="exportTasks" title="导出为 JSON">
                <span class="export-icon">📥</span>
                <span class="export-text">导出 JSON</span>
              </button>
            </div>
          </div>
        </div>
      </header>

            <div class="main-content">
                <div class="left-panel">
                    <!-- 折叠按钮组（窄屏幕） -->
                    <div class="toggle-buttons-group mobile-only">
                      <button 
                        class="toggle-section-btn" 
                        :class="{ 'active': showAddTask }"
                        @click="toggleSection('addTask')"
                      >
                        <span class="toggle-icon">➕</span>
                        <span>添加任务</span>
                      </button>
                      
                      <button 
                        class="toggle-section-btn" 
                        :class="{ 'active': showSearch }"
                        @click="toggleSection('search')"
                      >
                        <span class="toggle-icon">🔍</span>
                        <span>搜索筛选</span>
                      </button>
                      
                      <button 
                        v-if="allTasks.length > 0"
                        class="toggle-section-btn" 
                        :class="{ 'active': showStats }"
                        @click="toggleSection('stats')"
                      >
                        <span class="toggle-icon">📊</span>
                        <span>任务统计</span>
                      </button>
                    </div>
                    
                    <div class="task-form-card" :class="{ 'mobile-collapsed': !showAddTask }">
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
            <div class="date-input-wrapper">
              <input 
                type="date" 
                v-model="newTaskDueDate" 
                class="form-select date-input"
                id="new-task-date-input"
              />
              <label 
                v-if="!newTaskDueDate" 
                class="date-placeholder"
                @click="openDatePicker('new')"
              >
                截止日期
              </label>
              <span 
                v-if="newTaskDueDate" 
                class="date-display"
                @click="openDatePicker('new')"
              >
                {{ formatDate(newTaskDueDate) }}
              </span>
            </div>
          </div>
          
          <div class="input-row">
            <button @click="addTask" class="add-btn add-btn-full">
              <span class="btn-icon">📝</span>
              <span>添加</span>
            </button>
          </div>
        </div>
      </div>

                    <div class="controls-card" :class="{ 'mobile-collapsed': !showSearch }">
                        <div class="search-section">
              <div class="search-wrapper">
                <span class="search-icon">🔍</span>
                <input 
                  type="text" 
                  v-model="searchKeyword"
                  @input="handleSearch"
                  @keyup.enter="fetchTasks"
                  placeholder="搜索任务（标题、描述、分类）..." 
                  class="search-input"
                />
                <button 
                  v-if="searchKeyword"
                  @click="clearSearch"
                  class="clear-search-btn"
                  title="清除搜索"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div class="filter-section">
              <div class="filter-label">分类筛选</div>
              <div class="filter-buttons">
                <button 
                  @click="selectedCategory = null; fetchTasks()"
                  :class="['filter-btn', { active: selectedCategory === null }]"
                >
                  全部
                </button>
                <button 
                  v-for="cat in categories" 
                  :key="cat"
                  @click="selectedCategory = cat; fetchTasks()"
                  :class="['filter-btn', { active: selectedCategory === cat }]"
                >
                  {{ cat }}
                </button>
              </div>
            </div>
            
            <div class="filter-section">
              <div class="filter-label">日期筛选</div>
              <div class="filter-buttons">
                <button 
                  @click="selectedDateFilter = null; fetchTasks()"
                  :class="['filter-btn', { active: selectedDateFilter === null }]"
                >
                  全部
                </button>
                <button 
                  @click="selectedDateFilter = 'overdue'; fetchTasks()"
                  :class="['filter-btn', { active: selectedDateFilter === 'overdue' }]"
                >
                  已过期
                </button>
                <button 
                  @click="selectedDateFilter = 'today'; fetchTasks()"
                  :class="['filter-btn', { active: selectedDateFilter === 'today' }]"
                >
                  今天到期
                </button>
                <button 
                  @click="selectedDateFilter = 'tomorrow'; fetchTasks()"
                  :class="['filter-btn', { active: selectedDateFilter === 'tomorrow' }]"
                >
                  明天到期
                </button>
                <button 
                  @click="selectedDateFilter = 'this_week'; fetchTasks()"
                  :class="['filter-btn', { active: selectedDateFilter === 'this_week' }]"
                >
                  本周到期
                </button>
                <button 
                  @click="selectedDateFilter = 'this_month'; fetchTasks()"
                  :class="['filter-btn', { active: selectedDateFilter === 'this_month' }]"
                >
                  本月到期
                </button>
                <button 
                  @click="selectedDateFilter = 'no_due_date'; fetchTasks()"
                  :class="['filter-btn', { active: selectedDateFilter === 'no_due_date' }]"
                >
                  无截止日期
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

                    <div v-if="allTasks.length > 0" class="stats-panel" :class="{ 'mobile-collapsed': !showStats }">
            <div class="stats-panel-header">
              <h3 class="stats-panel-title">
                <span class="stats-icon">📊</span>
                <span>任务统计</span>
              </h3>
            </div>
            
            <div class="stats-panel-content">
                            <div class="stats-section">
                <div class="completion-circle-wrapper">
                  <svg class="completion-circle" viewBox="0 0 120 120">
                    <circle 
                      cx="60" 
                      cy="60" 
                      r="50" 
                      stroke="#e0e0e0" 
                      stroke-width="10" 
                      fill="none"
                    />
                    <circle 
                      cx="60" 
                      cy="60" 
                      r="50" 
                      stroke="url(#gradient)" 
                      stroke-width="10" 
                      fill="none"
                      :stroke-dasharray="`${2 * Math.PI * 50}`"
                      :stroke-dashoffset="`${2 * Math.PI * 50 * (1 - completionRate / 100)}`"
                      stroke-linecap="round"
                      transform="rotate(-90 60 60)"
                      class="completion-progress"
                    />
                    <defs>
                      <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#0f4c75;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#3282b8;stop-opacity:1" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div class="completion-text">
                    <span class="completion-percent">{{ completionRate }}%</span>
                    <span class="completion-label">完成率</span>
                  </div>
                </div>
              </div>

                            <div class="stats-section">
                <h4 class="stats-section-title">📁 按分类统计</h4>
                <div class="category-stats-list">
                  <div 
                    v-for="stat in categoryStats" 
                    :key="stat.category"
                    class="category-stat-item"
                  >
                    <div class="category-stat-header">
                      <span class="category-name">{{ stat.category }}</span>
                      <span class="category-count">{{ stat.completed }}/{{ stat.total }}</span>
                    </div>
                    <div class="progress-bar">
                      <div 
                        class="progress-fill" 
                        :style="{ width: `${stat.rate}%` }"
                      ></div>
                    </div>
                    <div class="category-rate">{{ stat.rate }}%</div>
                  </div>
                </div>
              </div>

                            <div class="stats-section">
                <h4 class="stats-section-title">⭐ 按优先级统计</h4>
                <div class="priority-stats-list">
                  <div 
                    v-for="stat in priorityStats.filter(s => s.total > 0)" 
                    :key="stat.label"
                    class="priority-stat-item"
                  >
                    <div class="priority-stat-header">
                      <span class="priority-icon" :style="{ color: stat.color }">
                        {{ stat.icon }} {{ stat.label }}
                      </span>
                      <span class="priority-count">{{ stat.completed }}/{{ stat.total }}</span>
                    </div>
                    <div class="progress-bar">
                      <div 
                        class="progress-fill" 
                        :style="{ 
                          width: `${stat.rate}%`,
                          background: `linear-gradient(90deg, ${stat.color} 0%, ${stat.color}dd 100%)`
                        }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

                <div class="right-panel">
                    <div v-if="loading" class="loading-card">
            <div class="spinner"></div>
            <span>加载中...</span>
          </div>

                    <section v-if="!loading && activeTasks.length" class="tasks-section">
            <div class="section-header">
              <button @click="showActiveTasks = !showActiveTasks" class="toggle-btn">
                <span class="section-icon">📋</span>
                <span>待处理任务</span>
                <span class="badge">{{ activeTasks.length }}</span>
                <span class="toggle-icon" :class="{ 'rotated': showActiveTasks }">▼</span>
              </button>
            </div>
            
            <transition name="slide">
              <div v-if="showActiveTasks">
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
                
                                <div v-if="editingTaskId === task.id" class="task-content edit-mode">
                  <div class="edit-form">
                    <input 
                      v-model="editForm.title" 
                      class="edit-input"
                      placeholder="任务标题..."
                      maxlength="255"
                    />
                    <textarea 
                      v-model="editForm.description" 
                      class="edit-textarea"
                      placeholder="描述（可选）..."
                      rows="2"
                      maxlength="1000"
                    ></textarea>
                    <div class="edit-options">
                      <div class="category-input-wrapper">
                        <input 
                          v-model="editForm.category" 
                          list="edit-category-list"
                          placeholder="选择或输入分类..." 
                          class="edit-select category-input"
                          maxlength="50"
                        />
                        <datalist id="edit-category-list">
                          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
                        </datalist>
                      </div>
                      <select v-model="editForm.priority" class="edit-select">
                        <option v-for="opt in priorityOptions" :key="opt.value" :value="opt.value">
                          {{ opt.icon }} {{ opt.label }}
                        </option>
                      </select>
                      <div class="date-input-wrapper">
                        <input 
                          type="date" 
                          v-model="editForm.due_date" 
                          class="edit-select date-input"
                          :id="`edit-task-date-input-${task.id}`"
                        />
                        <label 
                          v-if="!editForm.due_date" 
                          class="date-placeholder"
                          @click="openDatePicker('edit', task.id)"
                        >
                          截止日期
                        </label>
                        <span 
                          v-if="editForm.due_date" 
                          class="date-display"
                          @click="openDatePicker('edit', task.id)"
                        >
                          {{ formatDate(editForm.due_date) }}
                        </span>
                      </div>
                    </div>
                    <div class="edit-actions">
                      <button @click="saveEdit(task.id)" class="save-btn">保存</button>
                      <button @click="cancelEdit" class="cancel-btn">取消</button>
                    </div>
                  </div>
                </div>
                
                                <div v-else class="task-content">
                  <div class="task-title">{{ task.title }}</div>
                  <div v-if="task.description" class="task-description-wrapper">
                    <div 
                      class="task-description" 
                      :class="{ 'expanded': expandedDescriptions.has(task.id) }"
                    >
                      {{ task.description }}
                    </div>
                    <button 
                      v-if="shouldShowExpandButton(task.description)"
                      @click="toggleDescription(task.id)"
                      class="expand-description-btn"
                      :title="expandedDescriptions.has(task.id) ? '收起' : '展开'"
                    >
                      <span v-if="expandedDescriptions.has(task.id)">收起</span>
                      <span v-else>展开</span>
                      <span class="expand-icon" :class="{ 'expanded': expandedDescriptions.has(task.id) }">▼</span>
                    </button>
                  </div>
                  
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
                      :class="{ 
                        'overdue': isOverdue(task.due_date),
                        'today': getDaysDifference(task.due_date) === 0
                      }"
                    >
                      📅 {{ formatDate(task.due_date) }}
                    </span>
                  </div>
                </div>
                
                <div v-if="editingTaskId !== task.id" class="task-actions">
                  <button 
                    class="edit-btn" 
                    @click="startEdit(task)" 
                    title="编辑任务"
                  >
                    <span class="edit-icon">✏️</span>
                  </button>
                  <button 
                    class="delete-btn" 
                    @click="deleteTask(task.id)" 
                    title="删除任务"
                  >
                    <span class="delete-icon">🗑️</span>
                  </button>
                </div>
              </div>
                </transition-group>
                
                <!-- 懒加载触发器（不可见，用于Intersection Observer） -->
                <div v-if="hasMoreActiveTasks" class="load-more-trigger load-more-active"></div>
              </div>
            </transition>
          </section>

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
                  
                                    <div v-if="editingTaskId === task.id" class="task-content edit-mode">
                    <div class="edit-form">
                      <input 
                        v-model="editForm.title" 
                        class="edit-input"
                        placeholder="任务标题..."
                        maxlength="255"
                      />
                      <textarea 
                        v-model="editForm.description" 
                        class="edit-textarea"
                        placeholder="描述（可选）..."
                        rows="2"
                        maxlength="1000"
                      ></textarea>
                      <div class="edit-options">
                        <div class="category-input-wrapper">
                          <input 
                            v-model="editForm.category" 
                            list="edit-completed-category-list"
                            placeholder="选择或输入分类..." 
                            class="edit-select category-input"
                            maxlength="50"
                          />
                          <datalist id="edit-completed-category-list">
                            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
                          </datalist>
                        </div>
                        <select v-model="editForm.priority" class="edit-select">
                          <option v-for="opt in priorityOptions" :key="opt.value" :value="opt.value">
                            {{ opt.icon }} {{ opt.label }}
                          </option>
                        </select>
                        <div class="date-input-wrapper">
                          <input 
                            type="date" 
                            v-model="editForm.due_date" 
                            class="edit-select date-input"
                            :id="`edit-completed-task-date-input-${task.id}`"
                          />
                          <label 
                            v-if="!editForm.due_date" 
                            class="date-placeholder"
                            @click="openDatePicker('edit', task.id)"
                          >
                            截止日期
                          </label>
                          <span 
                            v-if="editForm.due_date" 
                            class="date-display"
                            @click="openDatePicker('edit', task.id)"
                          >
                            {{ formatDate(editForm.due_date) }}
                          </span>
                        </div>
                      </div>
                      <div class="edit-actions">
                        <button @click="saveEdit(task.id)" class="save-btn">保存</button>
                        <button @click="cancelEdit" class="cancel-btn">取消</button>
                      </div>
                    </div>
                  </div>
                  
                                    <div v-else class="task-content">
                    <div class="task-title">{{ task.title }}</div>
                    <div v-if="task.description" class="task-description-wrapper">
                      <div 
                        class="task-description" 
                        :class="{ 'expanded': expandedDescriptions.has(task.id) }"
                      >
                        {{ task.description }}
                      </div>
                      <button 
                        v-if="shouldShowExpandButton(task.description)"
                        @click="toggleDescription(task.id)"
                        class="expand-description-btn"
                        :title="expandedDescriptions.has(task.id) ? '收起' : '展开'"
                      >
                        <span v-if="expandedDescriptions.has(task.id)">收起</span>
                        <span v-else>展开</span>
                        <span class="expand-icon" :class="{ 'expanded': expandedDescriptions.has(task.id) }">▼</span>
                      </button>
                    </div>
                    
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
                  
                  <div v-if="editingTaskId !== task.id" class="task-actions">
                    <button 
                      class="edit-btn" 
                      @click="startEdit(task)" 
                      title="编辑任务"
                    >
                      <span class="edit-icon">✏️</span>
                    </button>
                    <button 
                      class="delete-btn" 
                      @click="deleteTask(task.id)" 
                      title="删除任务"
                    >
                      <span class="delete-icon">🗑️</span>
                    </button>
                  </div>
                </div>
                
                <!-- 懒加载触发器（不可见，用于Intersection Observer） -->
                <div v-if="hasMoreCompletedTasks" class="load-more-trigger load-more-completed"></div>
              </div>
            </transition>
          </section>
      
                    <div v-if="!loading && allTasks.length === 0" class="empty-state">
            <div class="empty-icon">🎉</div>
            <div class="empty-text">恭喜！目前没有待办事项</div>
            <div class="empty-subtext">添加你的第一个任务开始吧！</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 快速回到顶部按钮 -->
    <transition name="fade">
      <button 
        v-if="showScrollToTop"
        @click="scrollToTop"
        class="scroll-to-top-btn"
        title="回到顶部"
      >
        <span class="scroll-icon">↑</span>
      </button>
    </transition>
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
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 25%, #bbe1fa 50%, #1b262c 75%, #0f4c75 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  z-index: -1;
  opacity: 0.08;
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

.left-panel {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

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
}

.title-icon {
  font-size: 2.5rem;
  animation: bounce 2s infinite;
  display: inline-block;
  /* 确保 emoji 可见，不受父元素透明设置影响 */
  -webkit-text-fill-color: initial;
  color: initial;
}

.title-text {
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.stats {
  display: flex;
  gap: 15px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  /* 高度等于按钮容器高度：两个按钮高度 + gap（box-sizing: border-box 已包含padding） */
  height: calc((10px + 0.9rem * 1.5 + 10px) * 2 + 10px);
  box-sizing: border-box;
}

.stat-item:hover {
  transform: translateY(-5px) scale(1.05);
}

.stat-number {
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 0.85rem;
  color: #666;
  margin-top: 4px;
}

/* 已过期计数项样式 */
.stat-number-overdue {
  color: #ff4757 !important;
  -webkit-text-fill-color: #ff4757 !important;
  background: none !important;
  -webkit-background-clip: unset !important;
  background-clip: unset !important;
}

/* 统计面板 */
.stats-panel {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  animation: fadeInUp 0.6s ease-out;
}

.stats-panel-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}

.stats-panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
  color: #333;
}

.stats-icon {
  font-size: 1.3rem;
}

.stats-panel-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.stats-section {
  background: rgba(255, 255, 255, 0.6);
  padding: 20px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.stats-section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

/* 完成率圆形进度条 */
.completion-circle-wrapper {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 20px 0;
}

.completion-circle {
  width: 140px;
  height: 140px;
  transform: rotate(-90deg);
}

.completion-progress {
  transition: stroke-dashoffset 0.8s ease;
}

.completion-text {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.completion-percent {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.completion-label {
  font-size: 0.9rem;
  color: #666;
}

/* 分类统计 */
.category-stats-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-stat-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
}

.category-count {
  font-size: 0.85rem;
  color: #666;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0f4c75 0%, #3282b8 100%);
  border-radius: 4px;
  transition: width 0.6s ease;
}

.category-rate {
  font-size: 0.8rem;
  color: #999;
  text-align: right;
}

/* 优先级统计 */
.priority-stats-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.priority-stat-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.priority-stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.priority-icon {
  font-size: 0.95rem;
  font-weight: 600;
}

.priority-count {
  font-size: 0.85rem;
  color: #666;
}

.export-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  /* 计算总高度：两个按钮高度 + gap */
  height: calc((10px + 0.9rem * 1.5 + 10px) * 2 + 10px);
  box-sizing: border-box;
}

.export-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(15, 76, 117, 0.3);
  box-sizing: border-box;
  height: calc(10px + 0.9rem * 1.5 + 10px); /* 固定按钮高度 */
}

.export-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(15, 76, 117, 0.4);
}

.export-btn:active {
  transform: translateY(0);
}

.export-icon {
  font-size: 1.1rem;
}

.export-text {
  font-size: 0.9rem;
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
  border-color: #3282b8;
  box-shadow: 0 0 0 4px rgba(50, 130, 184, 0.1);
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

/* 编辑模式下优先级选择器使用固定宽度，为日期输入框留出更多空间 */
.edit-options select.edit-select {
  flex: 0 0 auto;
  width: 100px;
  min-width: 100px;
}

/* 日期输入框包装 */
.date-input-wrapper {
  flex: 1;
  min-width: 200px;
  position: relative;
}

.date-input {
  width: 100%;
  position: relative;
  z-index: 0;
  /* 确保高度与其他输入框一致 */
  box-sizing: border-box;
  transition: all 0.3s ease;
  /* 确保继承 form-select 的所有样式，特别是 padding */
  padding: 14px 18px;
  padding-right: 45px; /* 为日历图标留出空间 */
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  background: white;
  /* 确保高度由文字内容决定，与 form-select 完全一致 */
  line-height: 1.5;
  /* 移除浏览器默认样式 */
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  /* 确保内容区域高度正确 */
  display: block;
  /* 确保高度由文字内容决定，与 form-select 完全一致 */
  min-height: calc(1.5em + 28px + 4px); /* line-height + padding-top + padding-bottom + border */
}

/* 编辑模式下的日期输入框使用 edit-select 的 padding */
.edit-select.date-input {
  padding: 10px 14px;
  padding-right: 35px; /* 为日历图标留出空间 */
  border-radius: 8px;
  font-size: 0.95rem;
  min-height: calc(1.5em + 20px + 4px); /* line-height + padding-top + padding-bottom + border */
}

/* 日期输入框焦点效果，与其他输入框保持一致 */
.date-input:focus {
  outline: none;
  border-color: #3282b8;
  box-shadow: 0 0 0 4px rgba(50, 130, 184, 0.1);
  transform: translateY(-2px);
}

/* 完全隐藏原生日期输入框的显示（Chrome/Safari/Edge） */
.date-input::-webkit-datetime-edit-text,
.date-input::-webkit-datetime-edit-month-field,
.date-input::-webkit-datetime-edit-day-field,
.date-input::-webkit-datetime-edit-year-field {
  color: transparent !important;
}

.date-input::-webkit-datetime-edit {
  display: none;
}

.date-input::-webkit-calendar-picker-indicator {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  opacity: 0.6;
  z-index: 2;
  transition: all 0.3s ease;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.date-input::-webkit-calendar-picker-indicator:hover {
  opacity: 1;
}

/* 当输入框获得焦点时，日历图标也一起上移 */
.date-input:focus::-webkit-calendar-picker-indicator {
  transform: translateY(calc(-50% - 2px));
}

/* 自定义占位符 */
.date-placeholder {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  font-size: 1rem;
  user-select: none;
  z-index: 1;
  pointer-events: auto;
  cursor: pointer;
  transition: all 0.3s ease;
  line-height: 1.5;
}

/* 编辑模式下的占位符位置 */
.edit-select.date-input ~ .date-placeholder {
  left: 14px;
  font-size: 0.95rem;
}

/* 当输入框获得焦点时，占位符也一起上移 */
.date-input:focus ~ .date-placeholder {
  transform: translateY(calc(-50% - 2px));
}

/* 日期显示层（当选择了日期时显示） */
.date-display {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  color: #333;
  font-size: 1rem;
  user-select: none;
  z-index: 1;
  pointer-events: auto;
  cursor: pointer;
  font-weight: 500;
  line-height: 1.5;
  transition: all 0.3s ease;
  max-width: calc(100% - 50px); /* 留出右侧日历图标的空间 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 编辑模式下的日期显示层位置 */
.edit-select.date-input ~ .date-display {
  left: 14px;
  font-size: 0.95rem;
  max-width: calc(100% - 45px); /* 编辑模式下留出更多空间 */
}

/* 当输入框获得焦点时，日期显示层也一起上移 */
.date-input:focus ~ .date-display {
  transform: translateY(calc(-50% - 2px));
}

.date-display:hover {
  color: #3282b8;
}

/* Firefox 日期输入框样式 */
.date-input::-moz-placeholder {
  color: transparent;
  opacity: 0;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(15, 76, 117, 0.4);
  white-space: nowrap;
}

.add-btn-full {
  width: 100%;
  justify-content: center;
}

.add-btn:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(15, 76, 117, 0.5);
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

.search-section {
  width: 100%;
  margin-bottom: 0; /* 使用controls-card的gap来控制间距 */
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 16px;
  font-size: 1.2rem;
  z-index: 1;
}

.search-input {
  width: 100%;
  padding: 12px 16px 12px 48px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: white;
}

.search-input:focus {
  outline: none;
  border-color: #3282b8;
  box-shadow: 0 0 0 3px rgba(50, 130, 184, 0.1);
}

.clear-search-btn {
  position: absolute;
  right: 12px;
  width: 24px;
  height: 24px;
  border: none;
  background: #e0e0e0;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  color: #666;
  transition: all 0.2s ease;
}

.clear-search-btn:hover {
  background: #d0d0d0;
  transform: scale(1.1);
}

.filter-section,
.sort-section {
  flex: 1;
  min-width: 200px;
  margin-top: 0; /* 确保与搜索框的间距统一 */
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
  border-color: #3282b8;
  color: #3282b8;
  transform: translateY(-2px);
}

.filter-btn.active {
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 15px rgba(15, 76, 117, 0.3);
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
  border-color: #3282b8;
  box-shadow: 0 0 0 4px rgba(50, 130, 184, 0.1);
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
  border-top: 4px solid #3282b8;
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
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
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
  color: #3282b8;
}

.toggle-icon {
  transition: transform 0.3s ease;
  font-size: 0.9rem;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

/* 折叠按钮组样式 */
.toggle-buttons-group {
  display: none; /* 默认隐藏，只在窄屏幕显示 */
  flex-direction: row;
  gap: 10px;
  margin-bottom: 16px;
}

/* 折叠按钮样式 */
.toggle-section-btn {
  flex: 1;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 2px solid #e0e0e0;
  border-radius: 16px;
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.toggle-section-btn span:not(.toggle-icon) {
  font-size: 0.85rem;
  white-space: nowrap;
}

.toggle-section-btn:hover {
  border-color: #3282b8;
  box-shadow: 0 4px 12px rgba(50, 130, 184, 0.2);
  transform: translateY(-2px);
}

.toggle-section-btn:active {
  transform: translateY(0);
}

.toggle-section-btn .toggle-icon {
  font-size: 1.2rem;
  transition: all 0.3s ease;
}

/* 按钮激活状态样式 */
.toggle-section-btn.active {
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  border-color: transparent;
  color: white;
  box-shadow: 0 4px 15px rgba(15, 76, 117, 0.4);
}

.toggle-section-btn.active .toggle-icon {
  transform: scale(1.2);
}

.toggle-section-btn.active:hover {
  box-shadow: 0 6px 20px rgba(15, 76, 117, 0.5);
  transform: translateY(-2px) scale(1.02);
}

/* 宽屏幕下隐藏折叠按钮 */
@media (min-width: 992px) {
  .mobile-only {
    display: none !important;
  }
  
  .mobile-collapsed {
    display: block !important;
  }
  
  /* 宽屏幕下导入导出按钮也保持纵向排列 */
  .export-buttons {
    flex-direction: column; /* 保持纵向排列 */
    height: calc((10px + 0.9rem * 1.5 + 10px) * 2 + 10px); /* 两个按钮高度 + gap */
  }
  
  /* 宽屏幕下统计框高度匹配按钮容器高度（box-sizing: border-box 已包含padding） */
  .stat-item {
    height: calc((10px + 0.9rem * 1.5 + 10px) * 2 + 10px); /* 按钮容器高度 */
  }
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
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  transform: scaleY(0);
  transition: transform 0.3s ease;
}

.task-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: #3282b8;
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
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  border-color: transparent;
}

.task-checkbox:checked + .checkbox-label::after {
  transform: translate(-50%, -50%) scale(1);
}

.task-checkbox:focus + .checkbox-label {
  box-shadow: 0 0 0 4px rgba(50, 130, 184, 0.2);
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

.task-description-wrapper {
  margin-bottom: 10px;
}

.task-description {
  font-size: 0.9rem;
  color: #666;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap; /* 保留换行和空格 */
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3; /* 默认显示3行 */
  line-clamp: 3; /* 标准属性 */
  -webkit-box-orient: vertical;
  transition: all 0.3s ease;
}

.task-description.expanded {
  display: block;
  -webkit-line-clamp: unset;
  line-clamp: unset; /* 标准属性 */
  overflow: visible;
}

.expand-description-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  padding: 4px 8px;
  background: rgba(50, 130, 184, 0.1);
  border: 1px solid rgba(50, 130, 184, 0.2);
  border-radius: 6px;
  color: #3282b8;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.expand-description-btn:hover {
  background: rgba(50, 130, 184, 0.15);
  border-color: rgba(50, 130, 184, 0.3);
}

.expand-icon {
  font-size: 0.7rem;
  transition: transform 0.2s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
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
  background: rgba(50, 130, 184, 0.1);
  color: #3282b8;
}

.priority-tag {
  font-weight: 600;
}

.date-tag {
  background: rgba(0, 0, 0, 0.05);
  color: #666;
}

.date-tag.today {
  background: rgba(255, 193, 7, 0.15);
  color: #f57c00;
  font-weight: 600;
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

/* 编辑按钮 */
.task-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.edit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: rgba(50, 130, 184, 0.1);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
  opacity: 0.6;
}

.edit-btn:hover {
  background: rgba(50, 130, 184, 0.2);
  opacity: 1;
  transform: scale(1.1);
}

.edit-icon {
  font-size: 1.2rem;
}

/* 编辑表单 */
.edit-mode {
  width: 100%;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.edit-input,
.edit-textarea,
.edit-select {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  background: white;
  font-family: inherit;
}

.edit-input:focus,
.edit-textarea:focus,
.edit-select:focus {
  outline: none;
  border-color: #3282b8;
  box-shadow: 0 0 0 3px rgba(50, 130, 184, 0.1);
}

.edit-textarea {
  resize: vertical;
  min-height: 70px;
}

.edit-options {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.edit-options .edit-select {
  flex: 1;
  min-width: 120px;
}

/* 优先级选择器使用固定宽度，为日期输入框留出更多空间 */
.edit-options select.edit-select {
  flex: 0 0 auto;
  width: 100px;
  min-width: 100px;
}

.edit-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.save-btn,
.cancel-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.save-btn {
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(15, 76, 117, 0.3);
}

.save-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(15, 76, 117, 0.4);
}

.cancel-btn {
  background: #f0f0f0;
  color: #666;
}

.cancel-btn:hover {
  background: #e0e0e0;
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

/* 懒加载触发器（不可见，仅用于Intersection Observer） */
.load-more-trigger {
  height: 1px;
  margin: 20px 0;
  visibility: hidden;
  pointer-events: none;
}

/* 快速回到顶部按钮 */
.scroll-to-top-btn {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 1.5rem;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(15, 76, 117, 0.4);
  transition: all 0.3s ease;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scroll-to-top-btn:hover {
  transform: translateY(-5px) scale(1.1);
  box-shadow: 0 6px 20px rgba(15, 76, 117, 0.5);
}

.scroll-to-top-btn:active {
  transform: translateY(-3px) scale(1.05);
}

.scroll-icon {
  font-weight: bold;
  line-height: 1;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* -------------------------------------------------- */
/* 3. 响应式布局 (Media Queries) */
/* -------------------------------------------------- */

/* 针对大屏幕 (>= 992px) 的双栏布局 */
@media (min-width: 992px) {
    .main-content {
        /* 在大屏幕上启用两栏网格布局 */
        display: grid;
        grid-template-columns: 350px 1fr; /* 左侧固定宽度，右侧自适应 */
        gap: 30px;
    }

    .left-panel {
        /* 左侧面板在大屏幕下保持宽度，不限制高度 */
        position: sticky;
        top: 20px; /* 距离顶部留出空间 */
        align-self: flex-start; /* 从顶部开始对齐 */
    }

    .right-panel {
        /* 右侧面板在大屏幕上占据剩余空间 */
        width: 100%;
    }

    /* 优化头部统计在宽屏的布局 */
    .header-content {
        align-items: flex-end; /* 让统计信息对齐底部 */
        flex-wrap: nowrap; /* 避免在宽屏上统计信息换行 */
    }

    /* 宽屏上导出按钮文字可以显示 */
    .export-text {
        display: inline;
    }

    /* 调整筛选控件布局，让它们更紧凑 */
    .controls-card {
        flex-direction: column; /* 垂直排列搜索、筛选、排序部分 */
        gap: 20px;
    }
    
    .filter-section,
    .sort-section {
        min-width: unset; /* 取消最小宽度限制 */
        width: 100%; /* 占据父容器全部宽度 */
    }
    
    .filter-buttons {
        /* 筛选按钮区域可以继续保持换行 */
        justify-content: flex-start;
    }
    
    /* 统计面板在左侧，使用单列布局 */
    .left-panel .stats-panel-content {
        grid-template-columns: 1fr; /* 左侧统计面板使用单列 */
    }
}

/* 针对小屏幕 (<= 991px) 的优化 */
@media (max-width: 991px) {
    /* 显示折叠按钮组 */
    .toggle-buttons-group.mobile-only {
        display: flex !important;
    }
    
    /* 显示其他移动端元素 */
    .mobile-only:not(.toggle-buttons-group) {
        display: flex !important;
    }
    
    /* 默认折叠内容 */
    .mobile-collapsed {
        display: none !important;
    }
    
    /* 强制单栏布局 (默认就是，但显式写一下更清晰) */
    .main-content {
        flex-direction: column;
        gap: 20px;
    }
    
    /* 优化头部布局，在小屏幕上垂直排列 */
    .header-content {
        flex-direction: column;
        align-items: flex-start;
        gap: 20px;
    }
    
    .header-actions {
        width: 100%;
        flex-direction: column;
        align-items: flex-start;
        gap: 16px;
    }
    
    .stats {
        /* 让统计数据更紧凑 */
        gap: 10px;
        width: 100%;
        justify-content: flex-start;
    }
    
    .stat-item {
        padding: 8px 12px;
        border-radius: 12px;
        flex: 1;
        min-width: 0;
    }
    
    .export-buttons {
        width: 100%;
        flex-direction: row; /* 窄屏幕下横向排列，充分利用空间 */
        gap: 10px;
        flex-wrap: nowrap;
        height: auto; /* 取消固定高度 */
    }
    
    .export-btn {
        flex: 1; /* 让两个按钮平分宽度 */
        min-width: 0;
    }

    .stat-number {
        font-size: 1.5rem;
    }
    
    /* 小屏幕上保持文字显示，但调整按钮大小 */
    .export-text {
        display: inline; /* 保持文字显示 */
        font-size: 0.85rem; /* 稍微缩小字体 */
    }

    .export-btn {
        padding: 10px 12px; /* 调整内边距以适应文字 */
        white-space: nowrap; /* 防止文字换行 */
        height: auto; /* 自动高度 */
        min-height: calc(10px + 0.85rem * 1.5 + 10px); /* 最小高度 */
    }

    /* 优化新增任务表单输入行，确保在小屏幕上能换行 */
    .input-row {
        flex-direction: column;
        gap: 16px;
    }
    
    .task-input {
        min-width: auto;
    }
    
    .add-btn-full {
        width: 100%;
    }
    
    /* 确保日期、分类、优先级在小屏幕上各自占据一行 */
    .category-input-wrapper,
    .date-input-wrapper,
    .input-row select {
        min-width: 100%;
        width: 100%;
        flex-basis: 100%;
    }
    
    /* 筛选/排序卡片的布局 */
    .controls-card {
        flex-direction: column;
        gap: 20px;
    }
    
    /* 窄屏幕下排序方式全宽 */
    .sort-section {
        width: 100%;
        flex: none; /* 取消flex: 1，让宽度由width控制 */
    }
    
    .sort-select {
        width: 100%;
    }

    /* 统计面板优化 */
    .stats-panel-content {
        grid-template-columns: 1fr; /* 切换为单栏 */
    }
    
    /* 窄屏幕下调整回到顶部按钮位置 */
    .scroll-to-top-btn {
        bottom: 20px;
        right: 20px;
        width: 45px;
        height: 45px;
        font-size: 1.3rem;
    }
}


/* 针对超小屏幕 (<= 480px) 的进一步优化 */
@media (max-width: 480px) {
    .title {
        font-size: 2rem;
    }
    .title-icon {
        font-size: 2rem;
    }

    /* 头部统计信息更紧凑 */
    .stats {
        width: 100%;
        justify-content: space-between;
    }
    
    /* 超小屏幕下进一步优化导出按钮 */
    .export-btn {
        padding: 8px 10px; /* 更小的内边距 */
        font-size: 0.8rem; /* 更小的字体 */
    }
    
    .export-text {
        font-size: 0.8rem; /* 更小的文字 */
    }

    /* 确保筛选按钮换行时不会溢出 */
    .filter-buttons {
        justify-content: flex-start; /* 左对齐或开始换行 */
    }

    .filter-btn {
        padding: 8px 16px;
        font-size: 0.85rem;
    }
    
    /* 任务卡片在大屏幕上保持紧凑的 action 按钮 */
    .task-actions {
        flex-direction: column;
        gap: 6px;
    }
}
</style>