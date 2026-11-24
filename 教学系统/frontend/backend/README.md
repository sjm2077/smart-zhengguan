# 教学系统后端（Django REST Framework + MySQL）

本目录为教学系统后端初始实现，采用 Django、Django REST Framework、SimpleJWT 和 MySQL。前端位于仓库根目录。

## 1. 环境要求
- Python 3.11 或 3.12
- MySQL 8.x
- Node.js 环境用于启动现有 Vue 前端

## 2. 创建数据库
在 MySQL 中执行：
```sql
CREATE DATABASE college_teaching CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 3. 安装与配置（Windows PowerShell）
在仓库根目录执行：
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
编辑 `.env`，填写 MySQL 密码。请勿将真实密码或生产密钥提交到 Git。

若安装 `mysqlclient` 在本机失败，请先确认 Python 版本和 MySQL/MariaDB Connector/C 依赖匹配，再处理驱动安装；不要把数据库密码写入源码。

## 4. 初始化与启动
```powershell
python manage.py check
python manage.py makemigrations teaching
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

健康检查：`http://127.0.0.1:8000/api/health/`
管理后台：`http://127.0.0.1:8000/admin/`

## 5. 已提供的接口
- `POST /api/auth/login/`：登录，返回 `token`、`refresh`、`user`，兼容现有前端登录调用。
- `GET /api/auth/me/`：当前登录用户。
- `POST /api/auth/refresh/`：刷新 access token。
- `GET/POST/PUT/PATCH/DELETE /api/courses/`：课程管理。
- 同类 CRUD：`/api/teachers/`、`/api/students/`、`/api/exams/`、`/api/grades/`、`/api/notices/`。
- `/api/teaching-classes/`：教学班与任课安排。
- `/api/dashboard/summary/`、`/api/dashboard/semesters/`、`/api/dashboard/colleges/`。
- `/api/analysis/score-distribution/`、`course-scores/`、`semester-trend/`、`student-ranking/`。
- `GET /api/grades/statistics/`：成绩统计。

## 6. 当前阶段说明
该版本建立核心模型与接口基础，不会自动填充虚构教师、学生、成绩或预警数据。初始化后数据库为空，需通过 Django 管理后台或后续导入功能建立真实业务数据。权限基线为：认证用户可读，管理员和教务角色可写；正式部署前仍需按学院数据范围、教师任课范围、成绩审核/发布等流程补充细粒度权限与业务校验。
