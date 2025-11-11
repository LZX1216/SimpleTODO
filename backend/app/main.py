# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.database import engine, Base
from .models import task  # 导入模型以注册到 Base
from .core.config import settings

# 创建数据库表（如果不存在）
Base.metadata.create_all(bind=engine)

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

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Todo List API! Database setup complete."}