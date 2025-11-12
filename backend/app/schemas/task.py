# backend/app/schemas/task.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    """任务基础模型"""
    title: str = Field(..., min_length=1, max_length=255, description="任务标题")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")
    category: Optional[str] = Field("Misc", max_length=50, description="任务分类")


class TaskCreate(TaskBase):
    """创建任务的请求模型"""
    pass


class TaskUpdate(BaseModel):
    """更新任务的请求模型（所有字段都是可选的）"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    is_completed: Optional[bool] = None


class Task(TaskBase):
    """任务响应模型"""
    model_config = ConfigDict(from_attributes=True)  # 允许从 ORM 模型创建
    
    id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
