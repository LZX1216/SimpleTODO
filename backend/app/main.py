# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

from .core.database import engine, Base
from .models import task  # 导入模型以注册到 Base
from .core.config import settings
from .api import tasks

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 等待数据库就绪并创建表
def init_db():
    """初始化数据库，带重试机制"""
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"尝试连接数据库 (第 {attempt + 1}/{max_retries} 次)...")
            Base.metadata.create_all(bind=engine)
            logger.info("数据库连接成功，表创建完成")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"数据库连接失败: {e}，{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            else:
                logger.error(f"数据库连接失败，已达到最大重试次数: {e}")
                raise

# 初始化数据库
init_db()

app = FastAPI(
    title="Todo List API",
    version="1.0.0",
    description="RESTful API for Todo List application."
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(tasks.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Todo List API! Database setup complete."}