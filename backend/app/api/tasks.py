# backend/app/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

# 导入核心依赖和 CRUD 逻辑
from ..core.database import get_db
from .. import crud

# 显式导入 Pydantic 模型，确保路由签名和响应模型可以正确引用
from ..schemas.task import Task, TaskCreate, TaskUpdate 

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
    db: Session = Depends(get_db)
):
    """
    获取待办事项列表。
    
    - 支持按完成状态 (`is_completed`) 过滤。
    - 支持按任务分类 (`category`) 过滤。
    - 支持排序：`priority`（按优先级）、`due_date`（按截止日期）、默认按创建时间倒序。
    """
    tasks = crud.task.get_tasks(
        db=db, 
        is_completed=is_completed,
        category=category,
        sort_by=sort_by
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