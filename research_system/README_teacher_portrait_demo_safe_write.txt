教师画像模拟数据安全写入包 v1
项目：D:\research_system

重要：本包不会由 ChatGPT 直接连接或修改你的本地数据库。只有你在本地执行 apply 脚本并显式设置确认环境变量后，才会尝试写入。

一、写入对象与保护范围
- 计划来源：data_repair_plan\teacher_portrait_repair_v2\ 下的 v2 JSON/CSV。
- 预计新增：435 条 TeacherScore、44 条 Cooperation。
- 预计写入后：TeacherScore 由 85 条变为 520 条；Cooperation 由 28 条变为 72 条。
- 新增行：is_demo=True，data_source='TEACHER_PORTRAIT_DEMO_V1'。
- 写入器要求同时确认 UI 标签已就绪（TEACHER_PORTRAIT_DEMO_UI_LABEL_READY=YES），避免页面无标识地展示模拟数据。
- 既有行：不更新、不删除；迁移后默认 is_demo=False、data_source='existing'。
- 不新增/修改/删除 User、Project、Achievement、FundDetail 等其他业务记录。
- 所有写入放在一个 transaction.atomic() 事务中；事务内验证失败即回滚。
- 写入器默认拒绝写入；需要明确设置 TEACHER_PORTRAIT_DEMO_WRITE=APPLY_TEACHER_PORTRAIT_DEMO_V1。

二、先停止开发服务器
先在运行 runserver 的终端按 Ctrl+C，避免预检和写入过程中有其他进程同时改变数据库。
确认当前终端路径为 D:\research_system，且已激活 (venv)。

三、第一步：模型迁移前备份
将本包全部 .py 文件复制到 D:\research_system 项目根目录（与 manage.py 同级）。
执行：
python manage.py shell -c "exec(open('backup_teacher_portrait_before_migration_v1.py', encoding='utf-8').read())"

必须确认终端输出完整性检查为 ok，并保留 backups\teacher_portrait_demo_repair\ 中生成的 sqlite3 备份及同名 JSON 说明文件。

四、第二步：给两个模型增加演示标记
编辑 D:\research_system\api\models.py。在 TeacherScore 类和 Cooperation 类中分别增加下面两个字段（每个类都加一份）：

    # 演示数据标识；旧记录迁移后默认保留为非演示记录。
    is_demo = models.BooleanField(default=False, db_index=True, verbose_name='是否为演示数据')
    data_source = models.CharField(max_length=50, default='existing', db_index=True, verbose_name='数据来源')

请只在这两个模型中添加字段，不要替换整个 models.py。当前 FundBudget 已有 is_demo/data_source 的设计，可沿用相同字段命名。

然后执行：
python manage.py makemigrations api
python manage.py migrate

检查生成的迁移只包含 TeacherScore、Cooperation 的 is_demo 和 data_source 字段；若迁移涉及其他模型，先停止并检查迁移文件，不要直接 migrate。

五、第三步：先做独立预检（不写数据库）
确认以下四个文件来自本次 v2 运行，且都位于 data_repair_plan\teacher_portrait_repair_v2\：
- teacher_portrait_repair_plan.json
- teacher_score_candidates.csv
- cooperation_candidates.csv
- cooperation_unresolved_review.csv

特别注意：不要把旧版 data_repair_plan\teacher_portrait_repair\ 里的旧 CSV 混入 v2 文件夹。预检会校验 JSON/CSV 的 candidate_id、分数、教师身份、项目关联、重复关系和数据库当前状态。

执行：
python manage.py shell -c "exec(open('audit_teacher_portrait_demo_prewrite_v1.py', encoding='utf-8').read())"

只有输出状态 PASS 才能继续。报告：
data_repair_plan\teacher_portrait_repair_v2\teacher_portrait_demo_prewrite_audit.json

预检会在 backups\teacher_portrait_demo_repair\ 中创建一份写入前备份，并记录 SHA256。任何一项失败，都不要设置写入环境变量。

六、第四步：先完成 API/页面的演示标识，再考虑写入
数据库字段能区分模拟行，但当前教师画像接口/前端未必会显示标识。正式写入前必须先修改当前实际使用的 api/views.py 和相应前端页面：
- teacher_info / teacher_ability：返回 is_demo、data_source 或明确的 score_label；
- teacher_trend：逐年返回 score_is_demo，便于图表 tooltip 标注；
- cooperation_network：每条 link 返回 is_demo、data_source，tooltip 明确显示“演示数据（模拟）”；
- 页面上在评分卡片、趋势图和合作网络处显示“演示数据”标识；不能只在数据库标记。

完成上述修改并在本地确认标识能显示后，再阅读预检 JSON，确认 status=PASS、评分候选 435、合作候选 44、备份文件存在且 SHA256 已记录。

PowerShell 中执行（第二个变量是人为确认 UI 标识已就绪的安全门）：
$env:TEACHER_PORTRAIT_DEMO_UI_LABEL_READY = "YES"
$env:TEACHER_PORTRAIT_DEMO_WRITE = "APPLY_TEACHER_PORTRAIT_DEMO_V1"
python manage.py shell -c "exec(open('apply_teacher_portrait_demo_data_v1.py', encoding='utf-8').read())"
Remove-Item Env:TEACHER_PORTRAIT_DEMO_WRITE
Remove-Item Env:TEACHER_PORTRAIT_DEMO_UI_LABEL_READY

不要使用 generate_mock_data.py，也不要在此流程中运行会清空/重建全库的脚本。
如果写入脚本报错，保留终端完整报错和立即写入前备份；不要自行重复执行写入命令。

七、第五步：写入后独立只读复核
执行：
python manage.py shell -c "exec(open('verify_teacher_portrait_demo_postwrite_v1.py', encoding='utf-8').read())"

复核报告：
data_repair_plan\teacher_portrait_repair_v2\teacher_portrait_demo_postwrite_audit.json

预期：TeacherScore=520，Cooperation=72；本批次 is_demo=True 的评分=435、合作=44；Project=377、教师=104；原有非演示评分=85、合作=28。任何结果不符合预期，都应停止演示并先检查报告。

八、界面标识注意事项
数据库标记字段能明确区分模拟行，但当前接口/前端未必会自动显示标识。正式写入前，应在教师画像 API 中输出 is_demo/data_source，并在评分卡片、年度趋势、合作网络 tooltip 或图例中显示“演示数据”标签；不能只在数据库标记而让页面把模拟关系呈现成真实事实。

九、恢复原则
- 若仅需要撤销本批次数据，停止 runserver，使用“立即写入前备份”恢复到迁移后、写入前状态；先复制当前 db.sqlite3 作为事故留档，再恢复备份。
- 若迁移本身出错，停止 runserver，使用“迁移前备份”恢复数据库，并同时检查/回退相应模型迁移代码。
- 恢复前不要覆盖任何备份文件。请先保留当前数据库副本，再执行恢复操作。
