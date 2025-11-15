/**
 * 日期工具函数
 */

/**
 * 检查日期是否已过期
 * @param {string} dateString - 日期字符串
 * @returns {boolean} 是否已过期
 */
export const isOverdue = (dateString) => {
  if (!dateString) return false;
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  return date < today;
};

/**
 * 计算日期差（天数）
 * @param {string} dateString - 日期字符串
 * @returns {number} 天数差（负数表示已过期）
 */
export const getDaysDifference = (dateString) => {
  if (!dateString) return 0;
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  const diffTime = date - today;
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};

/**
 * 格式化日期显示
 * @param {string} dateString - 日期字符串
 * @returns {string} 格式化后的日期字符串
 */
export const formatDate = (dateString) => {
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

