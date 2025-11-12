# SimpleTODO
A simple To-Do List

## 开发说明

### 热重载配置

**不需要每次重启！** 项目已配置自动重载：

#### 后端（FastAPI + Docker）
- ✅ 已配置 `--reload` 选项，代码更改自动重载
- ✅ 已挂载代码目录到容器，文件更改实时同步
- **修改后端代码后，保存文件即可，无需重启 Docker**

#### 前端（Vue + Vite）
- ✅ Vite 默认支持热模块替换（HMR）
- **修改前端代码后，浏览器自动刷新，无需重启 npm**

### 启动项目

1. **启动后端（Docker）**：
   ```bash
   docker-compose up
   ```
   首次启动需要构建镜像，之后只需启动容器即可。

2. **启动前端（开发模式）**：
   ```bash
   cd frontend
   npm run dev
   ```

### 开发工作流

1. 启动 Docker 和 npm 一次
2. 修改代码 → 保存文件
3. 后端：自动重载（uvicorn --reload）
4. 前端：自动刷新（Vite HMR）
5. **无需手动重启！**

### 注意事项

- 如果修改了 `requirements.txt` 或 `Dockerfile`，需要重新构建：
  ```bash
  docker-compose build
  docker-compose up
  ```
- 如果修改了 `package.json`，需要重新安装依赖：
  ```bash
  cd frontend
  npm install
  ```