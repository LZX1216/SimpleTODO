# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Todo List API",
    version="1.0.0",
    description="RESTful API for Todo List application."
)

@app.get("/")
def read_root():
    # 验证服务是否启动
    return {"message": "Welcome to the FastAPI Todo List API! Service is running."}