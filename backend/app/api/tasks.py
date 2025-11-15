# backend/app/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

# 导入核心依赖和 CRUD 逻辑
from ..core.database import get_db
from .. import crud

# 显式导入 Pydantic 模型，确保路由签名和响应模型可以正确引用
from ..schemas.task import Task, TaskCreate, TaskUpdate
from pydantic import BaseModel 

# 路由器实例，所有任务相关的路由都将添加到这里
router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"], # 用于 Swagger UI 分组
)

# -----------------------------------------------------
# 1. CREATE: 添加待办事项 (POST /tasks/)
# -----------------------------------------------------
@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task_endpoint(task: TaskCreate, db: Session = Depends(get_db)):
    """
    添加一个新的待办事项。
    
    - title: 任务标题 (必填)
    - description: 任务描述 (可选)
    - category: 任务分类 (可选，默认 Misc)
    """
    # 需求细节决策：处理标题为空的情况
    if not task.title or task.title.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务标题不能为空。"
        )
    return crud.task.create_task(db=db, task=task)

# -----------------------------------------------------
# 2. READ: 查看待办事项列表 (GET /tasks/)
# -----------------------------------------------------
@router.get("/", response_model=List[Task])
def read_tasks_endpoint(
    is_completed: Optional[bool] = None, # 过滤条件：是否完成
    category: Optional[str] = None,      # 扩展过滤条件：分类
    sort_by: Optional[str] = None,        # 排序方式：priority, due_date, 或 None（默认创建时间）
    search: Optional[str] = None,        # 搜索关键词：在标题、描述、分类中搜索
    date_filter: Optional[str] = None,   # 日期筛选：overdue, today, tomorrow, this_week, this_month, no_due_date
    db: Session = Depends(get_db)
):
    """
    获取待办事项列表。
    
    - 支持按完成状态 (`is_completed`) 过滤。
    - 支持按任务分类 (`category`) 过滤。
    - 支持排序：`priority`（按优先级）、`due_date`（按截止日期）、默认按创建时间倒序。
    - 支持全文搜索 (`search`)：在标题、描述、分类中搜索关键词。
    - 支持日期筛选 (`date_filter`)：overdue（已过期）、today（今天到期）、tomorrow（明天到期）、this_week（本周到期）、this_month（本月到期）、no_due_date（无截止日期）。
    """
    tasks = crud.task.get_tasks(
        db=db, 
        is_completed=is_completed,
        category=category,
        sort_by=sort_by,
        search=search,
        date_filter=date_filter
    )
    return tasks

# -----------------------------------------------------
# 3. UPDATE: 标记完成/更新事项 (PATCH /tasks/{task_id})
# -----------------------------------------------------
@router.patch("/{task_id}", response_model=Task)
def update_task_endpoint(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """
    更新任务的标题、描述、分类或完成状态。
    """
    db_task = crud.task.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务未找到")
        
    return crud.task.update_task(db, db_task=db_task, task_update=task_update)

# -----------------------------------------------------
# 4. DELETE: 删除待办事项 (DELETE /tasks/{task_id})
# -----------------------------------------------------
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    """
    删除指定的待办事项。
    """
    db_task = crud.task.get_task(db, task_id=task_id)
    if db_task is None:
        # 如果找不到，抛出 404
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务未找到")
        
    crud.task.delete_task(db, db_task=db_task)
    # 返回 204 No Content，不需要返回 body
    return None

# -----------------------------------------------------
# 5. EXPORT: 导出所有任务数据 (GET /tasks/export)
# -----------------------------------------------------
@router.get("/export", response_class=JSONResponse)
def export_tasks_endpoint(db: Session = Depends(get_db)):
    """
    导出所有任务数据为 JSON 格式。
    
    返回包含所有任务数据的 JSON 对象，包括导出时间戳。
    """
    # 获取所有任务（不应用任何过滤）
    all_tasks = crud.task.get_tasks(db=db)
    
    # 转换为字典格式
    tasks_data = []
    for task in all_tasks:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "priority": task.priority,
            "is_completed": task.is_completed,
            "due_date": task.due_date.isoformat() if task.due_date is not None else None,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
        tasks_data.append(task_dict)
    
    # 构建导出数据
    export_data = {
        "export_time": datetime.now().isoformat(),
        "total_tasks": len(tasks_data),
        "tasks": tasks_data
    }
    
    return export_data

# -----------------------------------------------------
# 6. IMPORT: 批量导入任务数据 (POST /tasks/import)
# -----------------------------------------------------
class ImportTasksRequest(BaseModel):
    """导入任务的请求模型"""
    tasks: List[dict]  # 使用 dict 以支持 is_completed 字段

@router.post("/import", response_model=List[Task], status_code=status.HTTP_201_CREATED)
def import_tasks_endpoint(request: ImportTasksRequest, db: Session = Depends(get_db)):
    """
    批量导入任务数据。
    
    接收一个包含任务列表的JSON对象，格式：
    {
        "tasks": [
            {
                "title": "任务标题",
                "description": "任务描述（可选）",
                "category": "分类（可选）",
                "priority": 2,
                "due_date": "2024-01-01",
                "is_completed": false
            }
        ]
    }
    每个任务必须包含 title 字段，其他字段可选。
    """
    if not request.tasks or len(request.tasks) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务列表不能为空。"
        )
    
    tasks_data = request.tasks
    
    # 验证并转换任务数据
    task_creates = []
    for i, task_dict in enumerate(tasks_data):
        if not isinstance(task_dict, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"第 {i+1} 个任务数据格式错误。"
            )
        
        if not task_dict.get("title") or not str(task_dict.get("title")).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"第 {i+1} 个任务的标题不能为空。"
            )
        
        # 创建 TaskCreate 对象（不包含 is_completed）
        task_create = TaskCreate(
            title=task_dict["title"],
            description=task_dict.get("description"),
            category=task_dict.get("category"),
            priority=task_dict.get("priority"),
            due_date=task_dict.get("due_date")
        )
        task_creates.append(task_create)
    
    # 批量创建任务（传入原始数据以获取 is_completed）
    created_tasks = crud.task.create_tasks_batch(db=db, tasks=task_creates, tasks_data=tasks_data)
    
    return created_tasks