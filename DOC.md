# TODO List 项目说明文档

## 1. 技术选型
- **编程语言**：Python 3.12 ，理由：高效率、代码简洁，非常适合在短时间内实现高质量的 RESTful API。
- **框架/库**：FastAPI，理由：高性能异步框架，主动生成文档。  
- **数据库/存储**：MySQL (通过 Docker)，理由：稳定、成熟、支持复杂查询和事务。 
- **前端**：Vue 3 (Vite + 基础 JS/CSS)，理由：轻量级、易上手，适合快速开发简单界面。
- **部署方式**：Docker，理由：环境一致性，易于部署和扩展。
- 替代方案对比：例如为什么不用 MongoDB / 本地文件。  
  - Java (Spring Boot) 复杂度高，开发周期长，不适合本项目需求。  
  - SQLite 不适合前后端分离和未来的扩展需求。
  - 纯HTML/JS 缺乏结构化和可维护性，不适合复杂交互。
  - 直接部署在本地环境，缺乏可移植性和一致性，Docker 提供了更好的解决方案。

## 2. 项目结构设计
- 整体架构说明（前端/后端/数据库关系，或命令行工具的模块划分）。  
  - 采取前后端分离架构，前端负责用户交互和界面展示，后端进行数据处理和存储。数据库用于持久化存储任务数据。
- 目录结构示例：  
  ```
    SimpleTODO/
    ├── backend/                   # Python FastAPI 后端服务
    │   ├── app/                   # 核心应用代码
    │   │   ├── api/               # 路由和端点定义 (待实现)
    │   │   ├── core/              # 配置和数据库连接
    │   │   │   ├── config.py      # 应用配置
    │   │   │   └── database.py    # 数据库连接
    │   │   ├── models/            # SQLAlchemy ORM 模型
    │   │   │   └── task.py        # 任务数据模型
    │   │   └── main.py            # FastAPI 应用入口
    │   ├── venv/                  # Python 虚拟环境
    │   ├── Dockerfile             # 后端 Docker 镜像配置
    │   └── requirements.txt       # Python 依赖
    ├── frontend/                  # Vue 3 前端应用 (待实现)
    │   ├── src/
    │   │   ├── components/        # UI 组件
    │   │   └── views/             # 页面视图
    │   └── package.json           # 前端依赖
    ├── docker-compose.yml         # 定义后端和数据库服务
    ├── DOC.md                     # 项目说明文档
    └── README.md
  ```  
- 模块职责说明。  
  - **backend/app/main.py**: FastAPI 应用入口，初始化应用、配置 CORS、注册路由。
  - **backend/app/core/config.py**: 应用配置管理（数据库连接、CORS 设置等）。
  - **backend/app/core/database.py**: 数据库连接和会话管理，使用 SQLAlchemy ORM。
  - **backend/app/models/task.py**: SQLAlchemy 数据模型定义，对应数据库表结构。
  - **backend/app/api/**: RESTful API 路由定义，处理 HTTP 请求和响应（待实现）。
  - **frontend/src/components/**: Vue 3 组件，负责 UI 渲染和用户交互逻辑（待实现）。
  - **frontend/src/services/**: 前端 API 服务封装，通过 HTTP 请求调用后端接口（待实现）。

## 3. 需求细节与决策
- 描述是否必填？如何处理空输入？ 
  - 标题必填，描述可选。空输入时，标题为空则不允许添加，并给出提示；描述为空则存入空字符串。
- 已完成的任务在 UI 或 CLI 中如何显示？  
  - 在列表末尾,灰色样式显示。可通过 Filter/Tab 切换隐藏或显示已完成项。
- 任务优先级如何体现？（颜色区分 / 图标 / 排序）
  - 排序体现优先级，高优先级任务显示在前面。
- 任务排序逻辑（默认按创建时间，用户可选按优先级）。  
  - 默认排序：按创建时间降序 (最新创建的在最上面)。
  - 用户可选排序：按优先级 (高 -> 中 -> 低)，其次按截止日期 (近 -> 远)。
- 如果涉及扩展功能（例如同步/提醒），简述设计思路。  

## 4. AI 使用说明
- 使用 AI 工具（Gemini + Copilot + Cursor）  
- 使用 AI 的环节：
  - 文档初稿编写
  - 代码片段生成
  - Bug 定位与修复
- AI 输出如何修改：例如“AI 给出的方案用了 localStorage，我改成了 IndexedDB 以支持更复杂数据”。  

## 5. 运行与测试方式
- 本地运行方式（安装依赖、启动命令）。  
- 已测试过的环境（例如 Node.js v20，macOS）。  
- 已知问题与不足。  

## 6. 总结与反思
- 如果有更多时间，你会如何改进？  
- 你觉得这个实现的最大亮点是什么？  