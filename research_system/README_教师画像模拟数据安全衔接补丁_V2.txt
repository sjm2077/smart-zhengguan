教师画像模拟数据安全衔接补丁 V2
=====================================

本补丁针对教师画像新增的模拟年度评分与模拟合作关系，完成后端标记返回、前端醒目标注，并提供与现有写入器兼容的独立写入前预检脚本。

一、文件说明
------------
1. views.py
   - 教师画像基本信息、年度趋势、能力雷达接口返回 is_demo / data_source 等标识。
   - 教师画像合作网络逐条返回 is_demo / data_source，并统计原有记录和演示记录。
   - 全局年份、管理员绩效统计、学科绩效统计、普通项目详情默认排除教师画像演示数据，避免在未标注页面混用。
   - 不改变原有模型字段，也不要求新增迁移。

2. 智能分析教师版.html
   - 最新综合得分、近三年增长率、年度绩效趋势、绩效雷达图、合作网络均显示演示标识。
   - 趋势图中演示评分点使用黄色菱形；合作网络中演示关系使用黄色虚线。
   - 个人分析报告逐项标明演示评分/演示合作关系，不将其描述为真实考核或真实合作事实。

3. audit_teacher_portrait_demo_prewrite_v2.py
   - 只读检查计划 JSON、评分候选 CSV、合作候选 CSV、待复核 CSV。
   - 校验冻结基线、候选数量、教师/项目身份、评分范围及加权公式、重复教师年度键、重复合作关系。
   - 只有预检全部通过才创建独立 SQLite 备份，并在备份前后再次核对数据库状态。
   - 输出路径和 JSON 字段兼容现有 apply_teacher_portrait_demo_data_v1.py 写入器。
   - 不对业务数据库执行 INSERT、UPDATE 或 DELETE。

二、部署前保护
--------------
先在 D:\research_system 项目中备份现有 api\views.py 和教师画像 HTML 模板文件。
本补丁没有修改 models.py、urls.py 或 teacher_portrait_demo_safe_common_v1.py；不要用本补丁覆盖这些文件。

先定位项目中实际使用的模板文件，不要根据上传文件名猜路径：
    Get-ChildItem . -Recurse -Filter "智能分析教师版.html" | Select-Object FullName

将本补丁 views.py 的内容替换到：
    api\views.py

将本补丁 智能分析教师版.html 的内容替换到上一步定位到的实际模板文件。
将 audit_teacher_portrait_demo_prewrite_v2.py 放到项目根目录：
    D:\research_system\audit_teacher_portrait_demo_prewrite_v2.py

三、先做语法和 Django 配置检查
-------------------------------
在 PowerShell 中：
    python -m py_compile .\api\views.py .\audit_teacher_portrait_demo_prewrite_v2.py
    python manage.py check
    python manage.py showmigrations api

确认 0006_cooperation_data_source_cooperation_is_demo_and_more 已应用。
本补丁不需要再执行 makemigrations 或 migrate。

四、只读接口检查
----------------
选择一位教师的真实 ID 后，在浏览器或 API 客户端检查：
    /api/teacher/info?teacher_id=<教师ID>
    /api/teacher/trend?teacher_id=<教师ID>&type=all
    /api/teacher/ability?teacher_id=<教师ID>&year=<已有评分年份>
    /api/cooperation/network?teacher_id=<教师ID>

当前数据库仍是 85 条评分、28 条合作记录且演示记录为 0 时，页面不应凭空显示演示标识；接口应返回现有记录并带有标记字段。模拟记录写入后，相关指标、图表和报告才会显示“演示数据”。

五、写入前预检——此时不要执行正式写入
--------------------------------------
在确认后端/前端部署完成、页面无报错后，执行只读预检：
    python manage.py shell -c "exec(open('audit_teacher_portrait_demo_prewrite_v2.py', encoding='utf-8').read())"

预检必须显示 PASS，并生成：
    data_repair_plan\teacher_portrait_repair_v2\teacher_portrait_demo_prewrite_audit.json

检查报告中的 status、baseline_counts、候选数量、backup_path、backup_sha256。
如果出现 FAIL、数量与冻结基线不一致、备份失败或状态指纹变化，停止，不要运行正式写入器。

六、正式写入与写入后核验
------------------------
本补丁包不会自动写入数据库。暂时不要设置以下环境变量，也不要运行正式写入器，直到预检报告和页面标记已核对：
    TEACHER_PORTRAIT_DEMO_UI_LABEL_READY
    TEACHER_PORTRAIT_DEMO_WRITE

获得明确执行授权后，才按原有写入器的双重环境变量保护执行；执行后立即清除临时环境变量，并运行现有的：
    verify_teacher_portrait_demo_postwrite_v1.py

写入后预期仅新增 435 条标记为 TEACHER_PORTRAIT_DEMO_V1 的教师年度评分和 44 条标记为同一批次的合作关系；原有 85 条评分、28 条合作记录、104 位教师和 377 个项目均应保持不变。

七、静态检查结果
----------------
已对补丁进行以下静态检查：
- views.py：Python 语法检查通过。
- audit_teacher_portrait_demo_prewrite_v2.py：Python 语法检查通过。
- HTML 内联 JavaScript：Node.js --check 语法检查通过。

这些检查不替代你本机的 Django 检查、浏览器验收或数据库预检。
