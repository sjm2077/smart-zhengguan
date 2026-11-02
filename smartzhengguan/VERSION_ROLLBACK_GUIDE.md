# 版本回滚说明

## 当前开发分支
- **分支名称**: `feature/core-functions-r05-r07`
- **基于分支**: `feature/mock-data-integration`

## 已完成的功能
1. **R05 - 数据上传、自动识别与受控导入** (commit: 49346b3)
2. **R06 - 自定义学生名单与汇总表导出** (commit: 6065f4a)
3. **R07 - 可配置、可解释的主动预警规则引擎** (commit: fdb3eb1)

## 如何回滚

### 回滚到修改前（所有 R05-R07 功能之前）
```bash
# 切换回原始分支
git checkout feature/mock-data-integration

# 查看当前状态
git log --oneline -5
```

### 回滚到特定功能之前

#### 回滚到 R07 之前（保留 R05 和 R06）
```bash
git checkout feature/core-functions-r05-r07
git reset --hard 6065f4a
```

#### 回滚到 R06 之前（保留 R05）
```bash
git checkout feature/core-functions-r05-r07
git reset --hard 49346b3
```

#### 回滚到 R05 之前（删除所有新功能）
```bash
git checkout feature/core-functions-r05-r07
git reset --hard 20ec445
```

### 查看各个版本的提交记录
```bash
# 查看完整提交历史
git log --oneline --graph --all

# 查看特定提交的详细信息
git show 49346b3  # 查看 R05 的提交详情
git show 6065f4a  # 查看 R06 的提交详情
git show fdb3eb1  # 查看 R07 的提交详情
```

### 如果要保留当前工作，但临时切换到旧版本
```bash
# 保存当前工作
git stash save "临时保存当前工作"

# 切换到旧版本
git checkout 20ec445  # 或其他提交哈希

# 完成查看后，恢复工作
git checkout feature/core-functions-r05-r07
git stash pop
```

## 各版本功能对比

### 版本 1: 基础版本 (20ec445)
- ✅ 基础数据模型
- ✅ Mock 数据服务
- ✅ 系统页面和登录流程

### 版本 2: R05 - 数据上传 (49346b3)
- ✅ 文件上传与解析
- ✅ Sheet 识别
- ✅ 字段映射
- ✅ 数据校验与预览
- ✅ 导入批次管理

### 版本 3: R06 - 数据导出 (6065f4a)
- ✅ 可导出字段目录
- ✅ 自定义学生名单导出
- ✅ 汇总表导出
- ✅ 导出记录管理
- ✅ 导出模板管理

### 版本 4: R07 - 预警规则引擎 (fdb3eb1 - 当前版本)
- ✅ 预警规则 CRUD
- ✅ 规则版本管理
- ✅ 预警扫描引擎
- ✅ 预警实例管理
- ✅ 预警处理工作流
- ✅ 预警统计分析

## 数据库回滚

如果需要回滚数据库迁移：

### 查看当前迁移状态
```bash
cd backend
python manage.py showmigrations
```

### 回滚到特定迁移
```bash
# 回滚到 R07 之前
python manage.py migrate graduate 0005

# 回滚到 R06 之前
python manage.py migrate graduate 0004

# 回滚到 R05 之前
python manage.py migrate graduate 0003
```

### 完全重置数据库（谨慎使用）
```bash
# 删除数据库文件
rm db.sqlite3

# 重新运行所有迁移
python manage.py migrate

# 重新初始化数据
python manage.py seed_mock_data
python manage.py seed_field_catalog
python manage.py seed_warning_rules
```

## 注意事项

1. **数据备份**: 回滚前请确保备份重要数据
2. **代码冲突**: 如果有其他修改，回滚后可能需要手动解决冲突
3. **依赖关系**: R06 依赖 R05 的 FieldCatalog 模型，不建议单独删除 R05
4. **数据库同步**: 代码回滚后务必同步数据库迁移

## 联系信息

如有问题，请查看各个提交的详细信息：
```bash
git show 49346b3  # R05 详情
git show 6065f4a  # R06 详情
git show fdb3eb1  # R07 详情
```
