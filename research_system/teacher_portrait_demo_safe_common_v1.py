"""教师画像演示数据安全写入公共工具。仅供 D:\\research_system 项目内运行。"""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connection

PLAN_RELATIVE_DIR = Path("data_repair_plan") / "teacher_portrait_repair_v2"
BACKUP_RELATIVE_DIR = Path("backups") / "teacher_portrait_demo_repair"
DATA_SOURCE = "TEACHER_PORTRAIT_DEMO_V1"
WRITE_CONFIRM_ENV = "TEACHER_PORTRAIT_DEMO_WRITE"
WRITE_CONFIRM_VALUE = "APPLY_TEACHER_PORTRAIT_DEMO_V1"
UI_CONFIRM_ENV = "TEACHER_PORTRAIT_DEMO_UI_LABEL_READY"
UI_CONFIRM_VALUE = "YES"


def project_root() -> Path:
    return Path(settings.BASE_DIR).resolve()


def plan_dir() -> Path:
    return project_root() / PLAN_RELATIVE_DIR


def backup_dir() -> Path:
    return project_root() / BACKUP_RELATIVE_DIR


def input_paths() -> dict[str, Path]:
    base = plan_dir()
    return {
        "plan": base / "teacher_portrait_repair_plan.json",
        "scores": base / "teacher_score_candidates.csv",
        "cooperations": base / "cooperation_candidates.csv",
        "unresolved": base / "cooperation_unresolved_review.csv",
        "preflight": base / "teacher_portrait_demo_prewrite_audit.json",
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    temp_path.replace(path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sqlite_database_path() -> Path:
    if connection.vendor != "sqlite":
        raise RuntimeError(
            f"本安全包只支持当前项目的 SQLite 数据库；检测到 vendor={connection.vendor!r}，已拒绝继续。"
        )
    raw_name = connection.settings_dict.get("NAME")
    if not raw_name or str(raw_name) == ":memory:":
        raise RuntimeError("数据库路径为空或为内存数据库，无法生成可靠的独立备份。")
    path = Path(str(raw_name)).expanduser()
    if not path.is_absolute():
        path = project_root() / path
    path = path.resolve()
    if not path.is_file():
        raise RuntimeError(f"找不到当前 SQLite 数据库文件：{path}")
    return path


def backup_sqlite(prefix: str) -> dict:
    """通过 SQLite backup API 生成一致性备份，并检查完整性和表行数。"""
    source_path = sqlite_database_path()
    target_dir = backup_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    target_path = target_dir / f"{prefix}_{stamp}.sqlite3"
    if target_path.exists():
        raise RuntimeError(f"备份目标已存在，拒绝覆盖：{target_path}")

    source = None
    target = None
    try:
        source = sqlite3.connect(str(source_path), timeout=30)
        target = sqlite3.connect(str(target_path), timeout=30)
        source_tables = [
            row[0]
            for row in source.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        source_row_counts = {}
        for table_name in source_tables:
            quoted = '"' + table_name.replace('"', '""') + '"'
            source_row_counts[table_name] = source.execute(
                f"SELECT COUNT(*) FROM {quoted}"
            ).fetchone()[0]
        source.backup(target)
        target.commit()
        integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"备份数据库完整性检查失败：{integrity}")
        table_names = [
            row[0]
            for row in target.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        row_counts = {}
        for table_name in table_names:
            quoted = '"' + table_name.replace('"', '""') + '"'
            row_counts[table_name] = target.execute(
                f"SELECT COUNT(*) FROM {quoted}"
            ).fetchone()[0]
        if row_counts != source_row_counts:
            raise RuntimeError(
                f"备份与源数据库的表行数不一致：source={source_row_counts} backup={row_counts}"
            )
    except Exception:
        if target is not None:
            target.close()
            target = None
        if source is not None:
            source.close()
            source = None
        if target_path.exists():
            try:
                target_path.unlink()
            except OSError:
                pass
        raise
    finally:
        if target is not None:
            target.close()
        if source is not None:
            source.close()

    # 关闭后重新以只读方式打开，进行第二次完整性检查。
    uri = target_path.as_uri() + "?mode=ro"
    check = sqlite3.connect(uri, uri=True, timeout=30)
    try:
        integrity_after_close = check.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity_after_close != "ok":
            raise RuntimeError(f"备份关闭后复检失败：{integrity_after_close}")
    finally:
        check.close()

    report = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_database": str(source_path),
        "backup_path": str(target_path),
        "backup_sha256": sha256_file(target_path),
        "integrity_check": integrity_after_close,
        "source_table_row_counts": source_row_counts,
        "backup_table_row_counts": row_counts,
        "table_row_counts_match": row_counts == source_row_counts,
        "database_modified": False,
        "note": "通过 SQLite backup API 复制；未对源数据库执行 INSERT/UPDATE/DELETE。",
    }
    write_json(target_path.with_suffix(".json"), report)
    return report


def require_demo_marker_fields() -> None:
    from api.models import TeacherScore, Cooperation

    for model in (TeacherScore, Cooperation):
        for field_name in ("is_demo", "data_source"):
            try:
                model._meta.get_field(field_name)
            except Exception as exc:
                raise RuntimeError(
                    f"{model.__name__} 缺少字段 {field_name!r}。请先在 api/models.py 增加字段并执行迁移，不能直接写入。"
                ) from exc


def state_payload(include_demo_rows: bool = True) -> dict:
    """生成与本次写入有关的数据库状态快照；JSON 序列化时 Decimal 转字符串。"""
    from api.models import User, Project, TeacherScore, Cooperation

    scores = TeacherScore.objects.order_by("id")
    cooperations = Cooperation.objects.order_by("id")
    if not include_demo_rows:
        scores = scores.filter(is_demo=False)
        cooperations = cooperations.filter(is_demo=False)

    return {
        "teachers": list(
            User.objects.filter(role="teacher").order_by("id").values(
                "id", "real_name", "title", "dept_id"
            )
        ),
        "projects": list(
            Project.objects.order_by("id").values(
                "id", "project_no", "project_name", "leader_id", "dept_id"
            )
        ),
        "teacher_scores": list(
            scores.values(
                "id", "teacher_id", "year", "research_score", "teaching_score",
                "service_score", "comprehensive_score", "is_demo", "data_source"
            )
        ),
        "cooperations": list(
            cooperations.values(
                "id", "source", "target", "project_id", "coop_count", "is_demo", "data_source"
            )
        ),
    }


def state_fingerprint(include_demo_rows: bool = True) -> str:
    payload = state_payload(include_demo_rows=include_demo_rows)
    serialized = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def database_counts() -> dict[str, int]:
    from api.models import User, Project, TeacherScore, Cooperation

    return {
        "teachers_total": User.objects.filter(role="teacher").count(),
        "projects_total": Project.objects.count(),
        "teacher_score_records_total": TeacherScore.objects.count(),
        "cooperation_records_total": Cooperation.objects.count(),
        "teacher_score_demo_records": TeacherScore.objects.filter(is_demo=True).count(),
        "cooperation_demo_records": Cooperation.objects.filter(is_demo=True).count(),
    }


def pair_key(source, target) -> tuple[str, str]:
    left = str(source or "").strip().casefold()
    right = str(target or "").strip().casefold()
    return tuple(sorted((left, right)))


def decimal_text(value) -> str:
    from decimal import Decimal
    return format(Decimal(str(value)).quantize(Decimal("0.01")), ".2f")
