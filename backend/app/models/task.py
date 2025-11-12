# backend/app/models/task.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Date
from ..core.database import Base


class Task(Base):
    """任务数据模型"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)  # 标题（必填）
    description = Column(String(1000), default=None, nullable=True)  # 描述（可选）

    category = Column(String(50), index=True, default="Misc")  # 任务分类
    priority = Column(Integer, default=2, index=True)  # 优先级：1=高，2=中，3=低
    due_date = Column(Date, default=None, nullable=True, index=True)  # 截止日期
    is_completed = Column(Boolean, default=False)  # 完成状态

    created_at = Column(DateTime, default=func.now())  # 创建时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 更新时间