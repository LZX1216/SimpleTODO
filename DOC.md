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
    │   │   ├── api/               # 路由和端点定义
    │   │   │   └── tasks.py      # 任务相关的 API 路由
    │   │   ├── core/              # 配置和数据库连接
    │   │   │   ├── config.py      # 应用配置
    │   │   │   └── database.py    # 数据库连接
    │   │   ├── crud/              # 数据库操作逻辑
    │   │   │   └── task.py       # 任务的 CRUD 操作
    │   │   ├── models/            # SQLAlchemy ORM 模型
    │   │   │   └── task.py        # 任务数据模型
    │   │   ├── schemas/           # Pydantic 数据验证模型
    │   │   │   └── task.py        # 任务的请求/响应模型
    │   │   └── main.py            # FastAPI 应用入口
    │   ├── venv/                  # Python 虚拟环境
    │   ├── Dockerfile             # 后端 Docker 镜像配置
    │   └── requirements.txt       # Python 依赖
    ├── frontend/                  # Vue 3 前端应用
    │   ├── src/
    │   │   ├── App.vue            # 主应用组件（包含所有功能）
    │   │   ├── assets/            # 静态资源（CSS、图片等）
    │   │   ├── components/        # UI 组件（示例组件）
    │   │   └── main.js            # 应用入口
    │   ├── package.json           # 前端依赖
    │   └── vite.config.js         # Vite 配置
    ├── docker-compose.yml         # 定义后端和数据库服务
    ├── DOC.md                     # 项目说明文档
    └── README.md                  # 快速开始指南
  ```  
- 模块职责说明。  
  - **backend/app/main.py**: FastAPI 应用入口，初始化应用、配置 CORS、注册路由。
  - **backend/app/core/config.py**: 应用配置管理（数据库连接、CORS 设置等）。
  - **backend/app/core/database.py**: 数据库连接和会话管理，使用 SQLAlchemy ORM。
  - **backend/app/models/task.py**: SQLAlchemy 数据模型定义，对应数据库表结构。
  - **backend/app/schemas/task.py**: Pydantic 数据验证模型，用于请求验证和响应序列化。
  - **backend/app/crud/task.py**: 数据库 CRUD 操作逻辑，封装数据库查询和更新操作。
  - **backend/app/api/tasks.py**: RESTful API 路由定义，处理 HTTP 请求和响应。
  - **frontend/src/App.vue**: Vue 3 主应用组件，包含所有业务逻辑和 UI 渲染。
  - **frontend/src/assets/**: 全局样式和静态资源。

## 3. 需求细节与决策
- 描述是否必填？如何处理空输入？ 
  - 标题必填，描述可选。空输入时，标题为空则不允许添加，并给出提示；描述为空则存入 `null`（数据库字段为 nullable）。
  - 前端限制：标题最大 255 字符，描述最大 1000 字符，分类最大 50 字符。
- 已完成的任务在 UI 中如何显示？  
  - 已完成任务有独立的折叠区域，默认折叠。可通过按钮展开/折叠查看已完成任务。
  - 已完成任务使用灰色样式显示（opacity: 0.7），标题和描述有删除线。
- 任务优先级如何体现？（颜色区分 / 图标 / 排序）
  - 通过图标和颜色区分：🔥 高优先级（红色）、⚡ 中优先级（橙色）、💧 低优先级（绿色）。
  - 支持按优先级排序，高优先级任务显示在前面。
- 任务排序逻辑（默认按创建时间，用户可选按优先级）。  
  - 默认排序：按创建时间降序 (最新创建的在最上面)。
  - 用户可选排序：
    - 按优先级：高 -> 中 -> 低，相同优先级按创建时间降序。
    - 按截止日期：即将到期的在前，无截止日期的在最后，相同日期按优先级排序。
- 任务分类功能
  - 默认分类：工作、学习、生活、其他。
  - 支持自定义分类：用户可以在输入框中输入新分类名称。
  - 分类列表自动从数据库中实际存在的任务分类中提取，合并默认分类后显示。
  - 支持按分类筛选任务。
- 任务截止日期功能
  - 支持设置任务的截止日期（可选）。
  - 过期任务会显示红色警告样式，并有脉冲动画提醒。
  - 日期显示：今天显示"今天"，明天显示"明天"，过期显示"已过期"。
- 懒加载功能
  - 使用 Intersection Observer API 实现滚动懒加载。
  - 初始显示 10 条任务，滚动到底部时自动加载更多。
  - 待处理任务和已完成任务分别进行懒加载。  

## 4. AI 使用说明
- 使用 AI 工具（Gemini + Copilot + Cursor）  
- 使用 AI 的环节：
  - 使用 Gemini 讨论、分析、辅助技术选型
  - 使用 Gemini 和 Cursor 辅助编写 README.md, DOC.md
  - 使用 Gemini、Copilot、Cursor 生成代码片段，定位与修复bug
- AI 输出如何修改：例如“AI 给出的方案用了 localStorage，我改成了 IndexedDB 以支持更复杂数据”。  

## 5. 运行与测试方式
- 本地运行方式（安装依赖、启动命令）。  
  - **前置要求**：
    - Docker 和 Docker Compose（用于运行后端和数据库）
    - Node.js 16+ 和 npm（用于运行前端）
  
  - **启动步骤**：
    1. 启动后端和数据库（Docker）：
       ```bash
       docker-compose up
       ```
       首次启动需要构建镜像，之后只需启动容器即可。
       后端服务运行在 http://localhost:8000
       数据库运行在 localhost:3306
   
    2. 启动前端（开发模式）：
       ```bash
       cd frontend
       npm install  # 首次运行需要安装依赖
       npm run dev
       ```
       前端服务运行在 http://localhost:5173
  
  - **热重载配置**：
    - 后端：已配置 `--reload` 选项和代码目录挂载，修改后端代码后自动重载，无需重启 Docker。
    - 前端：Vite 默认支持热模块替换（HMR），修改前端代码后浏览器自动刷新，无需重启 npm。
  
  - **访问地址**：
    - 前端应用：http://localhost:5173
    - 后端 API：http://localhost:8000
    - API 文档（Swagger UI）：http://localhost:8000/docs
    - API 文档（ReDoc）：http://localhost:8000/redoc
  
  - **停止服务**：
    ```bash
    # 停止 Docker 服务
    docker-compose down
    
    # 停止前端（在运行前端的终端按 Ctrl+C）
    ```
  
  - **重新构建**：
    ```bash
    # 如果修改了 requirements.txt 或 Dockerfile
    docker-compose build
    docker-compose up
    
    # 如果修改了 package.json
    cd frontend
    npm install
    ```

- 已测试过的环境
  - Windows 11 (PowerShell)
  - Docker Desktop for Windows
  - Node.js v18+ / npm v9+
  - Python 3.12（在 Docker 容器中）
  - MySQL 8.0（在 Docker 容器中）

- 已知问题与不足
  - 前端和后端需要分别启动，没有统一的启动脚本。
  - 数据库数据存储在 Docker volume 中，删除容器后数据会保留，如需清空数据需要手动删除 volume。
  - 前端没有错误边界处理，某些错误可能导致整个应用崩溃。
  - 没有实现用户认证和授权，所有数据都是公开的。
  - 没有实现数据备份和恢复功能。  

## 6. 总结与反思
- 如果有更多时间，你会如何改进？  
- 你觉得这个实现的最大亮点是什么？  