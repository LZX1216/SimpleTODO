/**
 * 应用常量配置
 */

// 懒加载配置
export const LAZY_LOAD_BATCH_SIZE = 10; // 每次懒加载的任务数量
export const LAZY_LOAD_INITIAL_COUNT = 10; // 初始显示的任务数量

// 延迟时间配置（毫秒）
export const DATE_PICKER_DELAY = 10; // 日期选择器打开延迟
export const LAZY_LOAD_DELAY = 50; // 懒加载延迟
export const LAZY_LOAD_RENDER_DELAY = 150; // 懒加载渲染延迟
export const LAZY_LOAD_OBSERVER_DELAY = 50; // 懒加载观察器重新设置延迟
export const SETUP_LAZY_LOAD_DELAY = 200; // 设置懒加载观察器延迟
export const ON_MOUNT_LAZY_LOAD_DELAY = 100; // 组件挂载后设置懒加载延迟

// 字符长度限制
export const TITLE_MAX_LENGTH = 255; // 任务标题最大长度
export const DESCRIPTION_MAX_LENGTH = 1000; // 任务描述最大长度
export const CATEGORY_MAX_LENGTH = 50; // 分类名称最大长度
export const DESCRIPTION_EXPAND_THRESHOLD = 100; // 描述展开阈值（字符数）

// 动画延迟
export const TASK_ANIMATION_DELAY = 0.05; // 任务卡片动画延迟（秒）

// 滚动相关
export const SCROLL_TO_TOP_THRESHOLD = 300; // 显示回到顶部按钮的滚动距离（px）
export const INTERSECTION_OBSERVER_ROOT_MARGIN = '100px'; // Intersection Observer 的 rootMargin

