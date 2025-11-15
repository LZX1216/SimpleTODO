/**
 * 验证工具函数
 */

import { TITLE_MAX_LENGTH, DESCRIPTION_MAX_LENGTH, CATEGORY_MAX_LENGTH, DESCRIPTION_EXPAND_THRESHOLD } from './constants.js';

/**
 * 检查描述是否需要展开/收起按钮
 * @param {string} description - 描述内容
 * @returns {boolean} 是否需要展开按钮
 */
export const shouldShowExpandButton = (description) => {
  if (!description) return false;
  // 如果描述超过阈值字符数或者包含换行符，显示展开/收起按钮
  return description.length > DESCRIPTION_EXPAND_THRESHOLD || description.includes('\n');
};

/**
 * 验证任务标题
 * @param {string} title - 任务标题
 * @returns {{ valid: boolean, error?: string }} 验证结果
 */
export const validateTitle = (title) => {
  const trimmed = title.trim();
  if (!trimmed) {
    return { valid: false, error: '任务标题不能为空！' };
  }
  if (trimmed.length > TITLE_MAX_LENGTH) {
    return { valid: false, error: `任务标题不能超过${TITLE_MAX_LENGTH}个字符！` };
  }
  return { valid: true };
};

/**
 * 验证任务描述
 * @param {string} description - 任务描述
 * @returns {{ valid: boolean, error?: string }} 验证结果
 */
export const validateDescription = (description) => {
  if (!description) return { valid: true };
  const trimmed = description.trim();
  if (trimmed && trimmed.length > DESCRIPTION_MAX_LENGTH) {
    return { valid: false, error: `任务描述不能超过${DESCRIPTION_MAX_LENGTH}个字符！` };
  }
  return { valid: true };
};

/**
 * 验证分类名称
 * @param {string} category - 分类名称
 * @returns {{ valid: boolean, error?: string }} 验证结果
 */
export const validateCategory = (category) => {
  const trimmed = category.trim();
  if (trimmed && trimmed.length > CATEGORY_MAX_LENGTH) {
    return { valid: false, error: `分类名称不能超过${CATEGORY_MAX_LENGTH}个字符！` };
  }
  return { valid: true };
};

