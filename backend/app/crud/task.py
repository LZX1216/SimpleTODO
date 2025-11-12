# backend/app/crud/task.py
from sqlalchemy.orm import Session
from sqlalchemy import desc, case
from typing import List, Optional

from ..models.task import Task
from ..schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, task: TaskCreate) -> Task:
    """创建新任务"""
    db_task = Task(
        title=task.title,
        description=task.description,
        category=task.category or "Misc",
        priority=task.priority or 2,
        due_date=task.due_date
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(
    db: Session, 
    is_completed: Optional[bool] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = None
) -> List[Task]:
    """获取任务列表，支持按完成状态和分类过滤，支持排序"""
    query = db.query(Task)
    
    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)
    
    if category is not None:
        query = query.filter(Task.category == category)
    
    # 排序逻辑
    if sort_by == "priority":
        # 按优先级升序（1=高优先级在前），然后按创建时间倒序
        query = query.order_by(Task.priority.asc(), desc(Task.created_at))
    elif sort_by == "due_date":
        # 按截止日期升序（即将到期的在前），无截止日期的在最后，然后按优先级
        query = query.order_by(
            case((Task.due_date.is_(None), 1), else_=0),
            Task.due_date.asc(),
            Task.priority.asc(),
            desc(Task.created_at)
        )
    else:
        # 默认按创建时间倒序排列（最新的在前）
        query = query.order_by(desc(Task.created_at))
    
    return query.all()


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
