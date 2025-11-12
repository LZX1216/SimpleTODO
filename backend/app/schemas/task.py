# backend/app/schemas/task.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date


class TaskBase(BaseModel):
    """任务基础模型"""
    title: str = Field(..., min_length=1, max_length=255, description="任务标题")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")
    category: Optional[str] = Field("Misc", max_length=50, description="任务分类")
    priority: Optional[int] = Field(2, ge=1, le=3, description="优先级：1=高，2=中，3=低")
    due_date: Optional[date] = Field(None, description="截止日期")


class TaskCreate(TaskBase):
    """创建任务的请求模型"""
    pass


class TaskUpdate(BaseModel):
    """更新任务的请求模型（所有字段都是可选的）"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    priority: Optional[int] = Field(None, ge=1, le=3)
    due_date: Optional[date] = None
    is_completed: Optional[bool] = None


class Task(TaskBase):
    """任务响应模型"""
    model_config = ConfigDict(from_attributes=True)  # 允许从 ORM 模型创建
    
    id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
