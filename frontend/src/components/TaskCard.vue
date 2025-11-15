<script setup>
import { ref, computed, watch } from 'vue';
import { formatDate, isOverdue, getDaysDifference } from '../utils/dateUtils.js';
import { shouldShowExpandButton } from '../utils/validation.js';
import { TASK_ANIMATION_DELAY, TITLE_MAX_LENGTH, DESCRIPTION_MAX_LENGTH, CATEGORY_MAX_LENGTH } from '../utils/constants.js';

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    default: 0
  },
  isCompleted: {
    type: Boolean,
    default: false
  },
  isEditing: {
    type: Boolean,
    default: false
  },
  editForm: {
    type: Object,
    default: () => ({})
  },
  isDescriptionExpanded: {
    type: Boolean,
    default: false
  },
  categories: {
    type: Array,
    default: () => []
  },
  priorityOptions: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits([
  'toggle-completion',
  'start-edit',
  'save-edit',
  'cancel-edit',
  'delete-task',
  'toggle-description',
  'open-date-picker'
]);

const checkboxIdPrefix = computed(() => props.isCompleted ? 'completed' : 'task');

// 本地编辑表单（从 props 同步）
const localEditForm = ref({ ...props.editForm });
watch(() => props.editForm, (newForm) => {
  localEditForm.value = { ...newForm };
}, { deep: true });

// 优先级信息
const priorityInfo = computed(() => {
  return props.priorityOptions.find(opt => opt.value === (props.task.priority || 2)) || props.priorityOptions[1];
});

const isTaskOverdue = computed(() => isOverdue(props.task.due_date));
const isTaskToday = computed(() => getDaysDifference(props.task.due_date) === 0);
</script>

<template>
  <div 
    :class="['task-card', { 'completed': isCompleted }]"
    :style="{ animationDelay: `${index * TASK_ANIMATION_DELAY}s` }"
  >
    <div class="task-checkbox-wrapper">
      <input 
        type="checkbox" 
        :checked="task.is_completed" 
        @change="$emit('toggle-completion', task)"
        class="task-checkbox"
        :id="`${checkboxIdPrefix}-${task.id}`"
      />
      <label :for="`${checkboxIdPrefix}-${task.id}`" class="checkbox-label"></label>
    </div>
    
    <div v-if="isEditing" class="task-content edit-mode">
      <div class="edit-form">
        <input 
          v-model="localEditForm.title" 
          class="edit-input"
          placeholder="任务标题..."
          :maxlength="TITLE_MAX_LENGTH"
        />
        <textarea 
          v-model="localEditForm.description" 
          class="edit-textarea"
          placeholder="描述（可选）..."
          rows="2"
          :maxlength="DESCRIPTION_MAX_LENGTH"
        ></textarea>
        <div class="edit-options">
          <div class="category-input-wrapper">
            <input 
              v-model="localEditForm.category" 
              :list="`edit-category-list-${checkboxIdPrefix}`"
              placeholder="选择或输入分类..." 
              class="edit-select category-input"
              :maxlength="CATEGORY_MAX_LENGTH"
            />
            <datalist :id="`edit-category-list-${checkboxIdPrefix}`">
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </datalist>
          </div>
          <select v-model="localEditForm.priority" class="edit-select">
            <option v-for="opt in priorityOptions" :key="opt.value" :value="opt.value">
              {{ opt.icon }} {{ opt.label }}
            </option>
          </select>
          <div class="date-input-wrapper">
            <input 
              type="date" 
              v-model="localEditForm.due_date" 
              class="edit-select date-input"
              :id="`edit-${checkboxIdPrefix}-task-date-input-${task.id}`"
            />
            <label 
              v-if="!localEditForm.due_date" 
              class="date-placeholder"
              @click="$emit('open-date-picker', task.id)"
            >
              截止日期
            </label>
            <span 
              v-if="localEditForm.due_date" 
              class="date-display"
              @click="$emit('open-date-picker', task.id)"
            >
              {{ formatDate(localEditForm.due_date) }}
            </span>
          </div>
        </div>
        <div class="edit-actions">
          <button @click="$emit('save-edit', task.id, localEditForm)" class="save-btn">保存</button>
          <button @click="$emit('cancel-edit')" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>
    
    <div v-else class="task-content">
      <div class="task-title">{{ task.title }}</div>
      <div v-if="task.description" class="task-description-wrapper">
        <div 
          class="task-description" 
          :class="{ 'expanded': isDescriptionExpanded }"
        >
          {{ task.description }}
        </div>
        <button 
          v-if="shouldShowExpandButton(task.description)"
          @click="$emit('toggle-description', task.id)"
          class="expand-description-btn"
          :title="isDescriptionExpanded ? '收起' : '展开'"
        >
          <span v-if="isDescriptionExpanded">收起</span>
          <span v-else>展开</span>
          <span class="expand-icon" :class="{ 'expanded': isDescriptionExpanded }">▼</span>
        </button>
      </div>
      
      <div class="task-tags">
        <span class="tag category-tag">{{ task.category }}</span>
        <span 
          class="tag priority-tag" 
          :style="{ backgroundColor: priorityInfo.color + '20', color: priorityInfo.color }"
        >
          {{ priorityInfo.icon }} {{ priorityInfo.label }}
        </span>
        <span 
          v-if="task.due_date" 
          class="tag date-tag"
          :class="{ 
            'overdue': isTaskOverdue,
            'today': isTaskToday
          }"
        >
          📅 {{ formatDate(task.due_date) }}
        </span>
      </div>
    </div>
    
    <div v-if="!isEditing" class="task-actions">
      <button 
        class="edit-btn" 
        @click="$emit('start-edit', task)" 
        title="编辑任务"
      >
        <span class="edit-icon">✏️</span>
      </button>
      <button 
        class="delete-btn" 
        @click="$emit('delete-task', task.id)" 
        title="删除任务"
      >
        <span class="delete-icon">🗑️</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* 任务卡片样式 - 从 App.vue 复制 */
.task-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  gap: 16px;
  align-items: flex-start;
  transition: all 0.3s ease;
  animation: fadeInUp 0.4s ease-out;
  position: relative;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
}

.task-card.completed {
  opacity: 0.7;
}

.task-card.completed .task-title {
  text-decoration: line-through;
  color: #999;
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
  background: white;
}

.checkbox-label:hover {
  border-color: #3282b8;
  transform: scale(1.1);
}

.task-checkbox:checked + .checkbox-label {
  background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
  border-color: #3282b8;
}

.task-checkbox:checked + .checkbox-label::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 14px;
  font-weight: bold;
}

.task-content {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  word-break: break-word;
}

.task-description-wrapper {
  margin-bottom: 12px;
}

.task-description {
  font-size: 0.95rem;
  color: #666;
  line-height: 1.6;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-description.expanded {
  display: block;
  -webkit-line-clamp: unset;
}

.expand-description-btn {
  margin-top: 8px;
  padding: 4px 8px;
  background: rgba(50, 130, 184, 0.1);
  border: none;
  border-radius: 6px;
  color: #3282b8;
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s ease;
}

.expand-description-btn:hover {
  background: rgba(50, 130, 184, 0.2);
}

.expand-icon {
  font-size: 0.7rem;
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.task-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.tag {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
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

.date-tag.overdue {
  background: rgba(255, 71, 87, 0.1);
  color: #ff4757;
}

.date-tag.today {
  background: rgba(255, 165, 2, 0.1);
  color: #ffa502;
}

.task-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.edit-btn,
.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
  opacity: 0.6;
}

.edit-btn {
  background: rgba(50, 130, 184, 0.1);
}

.edit-btn:hover {
  background: rgba(50, 130, 184, 0.2);
  opacity: 1;
  transform: scale(1.1);
}

.delete-btn {
  background: rgba(255, 71, 87, 0.1);
}

.delete-btn:hover {
  background: rgba(255, 71, 87, 0.2);
  opacity: 1;
  transform: scale(1.1) rotate(90deg);
}

.edit-icon,
.delete-icon {
  font-size: 1.2rem;
}

/* 编辑模式样式 */
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

/* 分类输入框和日期输入框样式 */
.category-input-wrapper,
.date-input-wrapper {
  flex: 1;
  min-width: 200px;
  position: relative;
}

.category-input {
  width: 100%;
}

.date-input {
  width: 100%;
  position: relative;
  z-index: 0;
  box-sizing: border-box;
  transition: all 0.3s ease;
  padding: 10px 14px;
  padding-right: 35px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 0.95rem;
  background: white;
  line-height: 1.5;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  display: block;
  min-height: calc(1.5em + 20px + 4px);
}

.date-placeholder,
.date-display {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  font-size: 0.95rem;
  user-select: none;
  z-index: 1;
  pointer-events: auto;
  cursor: pointer;
  transition: all 0.3s ease;
  line-height: 1.5;
}

.date-display {
  color: #333;
  max-width: calc(100% - 45px);
}

.date-input:focus ~ .date-placeholder,
.date-input:focus ~ .date-display {
  transform: translateY(calc(-50% - 2px));
}

/* 下拉框箭头样式 */
select.edit-select,
.edit-select.category-input:not(.date-input),
input[list].edit-select:not(.date-input),
input[list].category-input.edit-select:not(.date-input) {
  appearance: none !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 9L1 4h10z'/%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 12px center !important;
  background-size: 12px !important;
  padding-right: 32px !important;
  cursor: pointer;
}

select.edit-select:hover,
.edit-select.category-input:not(.date-input):hover,
input[list].edit-select:not(.date-input):hover,
input[list].category-input.edit-select:not(.date-input):hover {
  border-color: #3282b8;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%233282b8' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
}

select.edit-select:focus,
.edit-select.category-input:not(.date-input):focus,
input[list].edit-select:not(.date-input):focus,
input[list].category-input.edit-select:not(.date-input):focus {
  outline: none;
  border-color: #3282b8;
  box-shadow: 0 0 0 3px rgba(50, 130, 184, 0.1);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%233282b8' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
}

.category-input-wrapper input[list].category-input {
  background-image: none !important;
  padding-right: 32px;
}

.category-input-wrapper:has(input[list])::after {
  content: '';
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-size: contain;
  pointer-events: none;
  z-index: 10;
  opacity: 1;
}

.category-input-wrapper:has(input[list]):hover::after,
.category-input-wrapper:has(input[list].category-input:focus)::after {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%233282b8' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

