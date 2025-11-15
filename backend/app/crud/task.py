# backend/app/crud/task.py
from sqlalchemy.orm import Session
from sqlalchemy import desc, case, or_
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
    sort_by: Optional[str] = None,
    search: Optional[str] = None,
    date_filter: Optional[str] = None
) -> List[Task]:
    """获取任务列表，支持按完成状态和分类过滤，支持排序，支持全文搜索，支持日期筛选"""
    from datetime import date, timedelta
    from sqlalchemy import and_, or_
    
    query = db.query(Task)
    
    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)
    
    if category is not None:
        query = query.filter(Task.category == category)
    
    # 日期筛选
    if date_filter:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)
        month_end = today + timedelta(days=30)
        
        if date_filter == "overdue":
            # 已过期：截止日期小于今天
            query = query.filter(Task.due_date < today)
        elif date_filter == "today":
            # 今天到期
            query = query.filter(Task.due_date == today)
        elif date_filter == "tomorrow":
            # 明天到期
            query = query.filter(Task.due_date == tomorrow)
        elif date_filter == "this_week":
            # 本周到期：今天到7天后
            query = query.filter(and_(Task.due_date >= today, Task.due_date <= week_end))
        elif date_filter == "this_month":
            # 本月到期：今天到30天后
            query = query.filter(and_(Task.due_date >= today, Task.due_date <= month_end))
        elif date_filter == "no_due_date":
            # 无截止日期
            query = query.filter(Task.due_date.is_(None))
    
    # 全文搜索：在标题、描述、分类中搜索关键词
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Task.title.like(search_term),
                Task.description.like(search_term),
                Task.category.like(search_term)
            )
        )
    
    # 排序逻辑
    if sort_by == "priority":
        # 按优先级升序（1=高优先级在前），然后按创建时间倒序
        query = query.order_by(Task.priority.asc(), desc(Task.created_at))
    elif sort_by == "due_date" or sort_by is None:
        # 按截止日期升序（即将到期的在前），无截止日期的在最后，然后按优先级
        # 这是默认排序方式
        query = query.order_by(
            case((Task.due_date.is_(None), 1), else_=0),
            Task.due_date.asc(),
            Task.priority.asc(),
            desc(Task.created_at)
        )
    else:
        # 其他情况：按创建时间倒序排列（最新的在前）
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


def create_tasks_batch(db: Session, tasks: List[TaskCreate], tasks_data: Optional[List[dict]] = None) -> List[Task]:
    """批量创建任务
    
    Args:
        db: 数据库会话
        tasks: TaskCreate 对象列表
        tasks_data: 原始任务数据字典列表（用于获取 is_completed 等额外字段）
    """
    db_tasks = []
    for i, task in enumerate(tasks):
        # 从原始数据中获取 is_completed（如果存在）
        is_completed = False
        if tasks_data and i < len(tasks_data):
            is_completed = tasks_data[i].get('is_completed', False)
        
        db_task = Task(
            title=task.title,
            description=task.description,
            category=task.category or "Misc",
            priority=task.priority or 2,
            due_date=task.due_date,
            is_completed=is_completed
        )
        db.add(db_task)
        db_tasks.append(db_task)
    
    db.commit()
    # 刷新所有任务以获取ID
    for db_task in db_tasks:
        db.refresh(db_task)
    
    return db_tasks
