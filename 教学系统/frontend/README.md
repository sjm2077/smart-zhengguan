# 高校智慧教学系统

基于 Vue 3 + Vite 的教学系统前端，后端采用 Django REST Framework，数据存储使用 MySQL。

## 项目结构

- `src/`：Vue 前端页面、路由与 API 调用。
- `backend/`：Django REST Framework 后端、数据模型、认证与 REST API。
- `vite.config.ts`：前端开发服务器配置，默认将 `/api` 代理到 `http://localhost:8000`。

## 前端启动

在仓库根目录执行：

```powershell
npm install
npm run dev
```

默认访问 `http://localhost:5173`。

## 后端启动

详细步骤见 [backend/README.md](backend/README.md)。简要流程：

1. 创建 MySQL 数据库 `college_teaching`，字符集使用 `utf8mb4`。
2. 进入 `backend/`，创建并激活 Python 虚拟环境。
3. 安装 `requirements.txt`，将 `.env.example` 复制为 `.env` 并填写数据库凭据。
4. 执行 `python manage.py makemigrations teaching`、`python manage.py migrate`。
5. 创建管理员账号并启动 `python manage.py runserver 0.0.0.0:8000`。

健康检查地址：`http://127.0.0.1:8000/api/health/`。

## 当前开发状态

Django 后端基础结构、核心教学数据模型、JWT 登录、基础 CRUD、仪表盘统计和成绩分析接口已加入独立开发分支。初始化后数据库不会自动写入虚构的业务数据；教师、学生、课程、成绩等数据需要经管理后台或后续导入流程维护。

当前后端仍处于开发阶段，正式使用前需要在本地完成依赖安装、迁移生成、接口联调和权限验证。请勿将 `.env`、数据库密码或生产密钥提交到版本库。
