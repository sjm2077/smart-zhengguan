# 教学系统后端权限修复（手动替换前请备份）

## 本次修改

- `permissions.py`：未配置用户档案的账号不再默认获得 viewer 权限；学生仅能查询自己的已发布成绩；教师成绩范围按其教学班关联课程限制；写操作仍只允许 admin / academic。
- `views.py`：学生、教师的学生/课程/教学班/考试/成绩查询按身份缩小范围；成绩统计、总览和趋势使用相同范围；学生不能读取全校学生排名。
- `serializers.py`：用户档案缺失时返回 `unassigned`；学期接口增加已存在的 academic_year/term 字段；成绩接口返回考试关联信息。

## 重要限制

旧数据库没有教学班记录。迁移后，教师查询课程、教学班、学生和成绩时会按当前教学班关系限制；在管理员建立教学班前，教师相关课程和成绩查询可能为空。这是有意的安全默认，不应通过放开全表查询来规避。

学生账号中只有唯一匹配到学生档案的账号会自动关联。其余学生账号在人工确认并关联档案前，成绩列表为空。

## 替换步骤

1. 先备份当前三个文件：
   - `backend/teaching/permissions.py`
   - `backend/teaching/views.py`
   - `backend/teaching/serializers.py`
2. 将压缩包中的三个文件分别复制到同一路径覆盖。
3. 在 `frontend\backend` 目录执行：
   ```powershell
   .\.venv\Scripts\python.exe -m py_compile .\teaching\permissions.py .\teaching\views.py .\teaching\serializers.py
   .\.venv\Scripts\python.exe manage.py check
   ```
4. 把完整输出发回核对。此时仍不要执行旧数据库导入的 `--execute`。

本包没有执行数据库迁移，也没有修改数据库记录。
