# backend/app/crud/task.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from ..models.task import Task
from ..schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, task: TaskCreate) -> Task:
    """创建新任务"""
    db_task = Task(
        title=task.title,
        description=task.description,
        category=task.category or "Misc"
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(
    db: Session, 
    is_completed: Optional[bool] = None,
    category: Optional[str] = None
) -> List[Task]:
    """获取任务列表，支持按完成状态和分类过滤"""
    query = db.query(Task)
    
    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)
    
    if category is not None:
        query = query.filter(Task.category == category)
    
    # 按创建时间倒序排列（最新的在前）
    return query.order_by(desc(Task.created_at)).all()


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """根据 ID 获取单个任务"""
    return db.query(Task).filter(Task.id == task_id).first()


def update_task(db: Session, db_task: Task, task_update: TaskUpdate) -> Task:
    """更新任务"""
    update_data = task_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, db_task: Task) -> None:
    """删除任务"""
    db.delete(db_task)
    db.commit()
