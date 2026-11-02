"""迁移前数据库专用备份。只备份 SQLite，不修改数据库内容。"""
from teacher_portrait_demo_safe_common_v1 import backup_sqlite

result = backup_sqlite("db_before_teacher_portrait_demo_migration")
print("=" * 76)
print("教师画像演示数据：迁移前数据库备份完成")
print("源数据库：", result["source_database"])
print("备份文件：", result["backup_path"])
print("SHA256：", result["backup_sha256"])
print("完整性检查：", result["integrity_check"])
print("数据库写入：否")
print("=" * 76)
