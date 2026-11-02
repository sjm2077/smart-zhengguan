"""data/ 目录真实 CSV 批量导入 zhhengguan_research。

用法: python scripts/import_real_data.py

导入以下真实采集数据:
  - CNKI 知网论文 (GBK 编码，55 行)
  - Guanwang 官网新闻 (UTF-8，485 行)
  - Score_Result 教师 7 维评分 (104 行)
  - Teacher_papers 教师论文分项 (104 行)
  - teacher_awards 教师获奖 (104 行)
  - Teacher_research 教师科研分项 (GBK，104 行)

已存在的项目/经费/成果表保持不动（那部分是科研系统自有数据）。
"""
from __future__ import annotations

import csv
import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path

import pymysql

# ---- 路径 ----
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

# ---- DB 连接 ----
DB_HOST = os.getenv("IMPORT_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("IMPORT_DB_PORT", "3306"))
DB_USER = os.getenv("IMPORT_DB_USER", "root")
DB_PASS = os.getenv("IMPORT_DB_PASS", "root")
DB_NAME = os.getenv("IMPORT_DB_NAME", "zhhengguan_research")


def get_conn():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset="utf8mb4", autocommit=True,
    )


def ensure_tables(cur):
    """创建 6 张新表（已存在则跳过）。"""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_realteacherscore (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_name VARCHAR(100),
            year INT DEFAULT 2024,
            course_score DECIMAL(6,2) DEFAULT 0,
            paper_score DECIMAL(6,2) DEFAULT 0,
            research_score DECIMAL(6,2) DEFAULT 0,
            partjob_score DECIMAL(6,2) DEFAULT 0,
            award_score DECIMAL(6,2) DEFAULT 0,
            eduachievement_score DECIMAL(6,2) DEFAULT 0,
            sum_score DECIMAL(6,2) DEFAULT 0,
            INDEX idx_name (teacher_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_teacheraward (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_name VARCHAR(100),
            award_name VARCHAR(200),
            score DECIMAL(6,2) DEFAULT 0,
            INDEX idx_name (teacher_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_cnkipaper (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(500),
            authors VARCHAR(500),
            journal VARCHAR(200),
            publish_date VARCHAR(32),
            source_file VARCHAR(100),
            INDEX idx_date (publish_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_guanwangnews (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url_hash VARCHAR(32) UNIQUE,
            title VARCHAR(512),
            publish_date VARCHAR(32),
            url VARCHAR(512),
            source_file VARCHAR(100),
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_hash (url_hash),
            INDEX idx_date (publish_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_teacherpaper (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_name VARCHAR(100),
            a_plus INT DEFAULT 0, a INT DEFAULT 0, b INT DEFAULT 0, c INT DEFAULT 0, d INT DEFAULT 0,
            academic_book_score DECIMAL(6,2) DEFAULT 0,
            thinktank_score DECIMAL(6,2) DEFAULT 0,
            total_score DECIMAL(6,2) DEFAULT 0,
            INDEX idx_name (teacher_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_guanwangpaper (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url_hash VARCHAR(32) UNIQUE,
            title VARCHAR(500),
            abstract LONGTEXT,
            keywords VARCHAR(500),
            fund_source VARCHAR(500),
            doi VARCHAR(200),
            journal VARCHAR(200),
            url VARCHAR(512),
            source_file VARCHAR(100),
            INDEX idx_hash (url_hash),
            INDEX idx_journal (journal)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_teacherresearch (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_name VARCHAR(100),
            project_count INT DEFAULT 0,
            research_score DECIMAL(6,2) DEFAULT 0,
            INDEX idx_name (teacher_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_teachingcourse (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_code VARCHAR(32),
            course_name VARCHAR(200),
            credit DECIMAL(5,1) DEFAULT 0,
            hours INT DEFAULT 0,
            course_type VARCHAR(32),
            INDEX idx_type (course_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_teachingteacher (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_no VARCHAR(32),
            teacher_name VARCHAR(100),
            gender VARCHAR(8),
            title VARCHAR(64),
            INDEX idx_title (title)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_teachinggrade (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_code VARCHAR(32),
            course_name VARCHAR(200),
            grade_type VARCHAR(32),
            score DECIMAL(6,2) DEFAULT 0,
            semester_id INT DEFAULT 0,
            INDEX idx_type (grade_type),
            INDEX idx_sem (semester_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


# ---- 各表导入函数 ----

def import_cnki(cur):
    f = DATA_DIR / "CNKI_山东大学 政治与公共管理学院.csv"
    if not f.exists():
        print("[CNKI] 文件不存在，跳过")
        return 0
    # CNKI 是 GBK 编码，无表头
    rows = []
    with open(f, "r", encoding="gbk", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            # CNKI CSV 字段用 \t 分隔: 题名\t作者\t期刊\t日期
            parts = line.split("\t")
            if len(parts) >= 4:
                rows.append((parts[0][:500], parts[1][:500], parts[2][:200], parts[3][:32], f.name))
            elif len(parts) >= 3:
                rows.append((parts[0][:500], parts[1][:500], parts[2][:200], "", f.name))

    cur.execute("DELETE FROM api_cnkipaper")
    cur.executemany(
        "INSERT INTO api_cnkipaper (title, authors, journal, publish_date, source_file) VALUES (%s,%s,%s,%s,%s)",
        rows,
    )
    print(f"[CNKI] 导入 {len(rows)} 条")
    return len(rows)


def import_guanwang(cur):
    """Guanwang_papers_full_sum.csv 实为学院官网论文题录（GBK 编码）。

    字段: 标题,摘要,关键词,资金来源,DOI,原文刊载于,原文链接
    """
    f = DATA_DIR / "Guanwang_papers_full_sum.csv"
    if not f.exists():
        print("[Guanwang] 文件不存在，跳过")
        return 0
    rows = []
    seen = set()
    with open(f, "r", encoding="gbk", errors="replace") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            title = (r.get("标题") or "").strip()
            if not title:
                continue
            url = (r.get("原文链接") or "").strip()
            h = hashlib.md5((url or title).encode("utf-8")).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            rows.append((
                h,
                title[:500],
                (r.get("摘要") or "").strip(),
                (r.get("关键词") or "").strip()[:500],
                (r.get("资金来源") or "").strip()[:500],
                (r.get("DOI") or "").strip()[:200],
                (r.get("原文刊载于") or "").strip()[:200],
                url[:512],
                f.name,
            ))

    cur.execute("DELETE FROM api_guanwangpaper")
    cur.executemany(
        """INSERT IGNORE INTO api_guanwangpaper
        (url_hash, title, abstract, keywords, fund_source, doi, journal, url, source_file)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows,
    )
    print(f"[Guanwang-Paper] 导入 {len(rows)} 条")
    return len(rows)


def import_score_result(cur):
    f = DATA_DIR / "Score_Result.csv"
    if not f.exists():
        print("[Score_Result] 文件不存在，跳过")
        return 0
    rows = []
    with open(f, "r", encoding="gbk", errors="replace") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            name = r.get("姓名", "").strip()
            if not name:
                continue
            rows.append((
                name[:100], 2024,
                float(r.get("course_score", 0) or 0),
                float(r.get("paper_score", 0) or 0),
                float(r.get("research_score", 0) or 0),
                float(r.get("partjob_score", 0) or 0),
                float(r.get("award_score", 0) or 0),
                float(r.get("eduachievement_score", 0) or 0),
                float(r.get("sum_score", 0) or 0),
            ))

    cur.execute("DELETE FROM api_realteacherscore")
    cur.executemany(
        """INSERT INTO api_realteacherscore
        (teacher_name, year, course_score, paper_score, research_score,
         partjob_score, award_score, eduachievement_score, sum_score)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows,
    )
    print(f"[Score_Result] 导入 {len(rows)} 条")
    return len(rows)


def import_teacher_papers(cur):
    f = DATA_DIR / "Teacher_papers.csv"
    if not f.exists():
        print("[Teacher_papers] 文件不存在，跳过")
        return 0
    rows = []
    with open(f, "r", encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            name = r.get("姓名", "").strip()
            if not name:
                continue
            rows.append((
                name[:100],
                int(float(r.get("A+", 0) or 0)),
                int(float(r.get("A", 0) or 0)),
                int(float(r.get("B", 0) or 0)),
                int(float(r.get("C", 0) or 0)),
                int(float(r.get("D", 0) or 0)),
                float(r.get("学术著作总分", 0) or 0),
                float(r.get("智库成果总分", 0) or 0),
                float(r.get("学术论文总分", 0) or 0),
            ))

    cur.execute("DELETE FROM api_teacherpaper")
    cur.executemany(
        """INSERT INTO api_teacherpaper
        (teacher_name, a_plus, a, b, c, d, academic_book_score, thinktank_score, total_score)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows,
    )
    print(f"[Teacher_papers] 导入 {len(rows)} 条")
    return len(rows)


def import_teacher_awards(cur):
    f = DATA_DIR / "teacher_awards_20240.csv"
    if not f.exists():
        print("[teacher_awards] 文件不存在，跳过")
        return 0
    rows = []
    with open(f, "r", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            name = r.get("Teacher", "").strip()
            if not name:
                continue
            rows.append((
                name[:100],
                r.get("Award", "")[:200],
                float(r.get("Score", 0) or 0),
            ))

    cur.execute("DELETE FROM api_teacheraward")
    cur.executemany(
        "INSERT INTO api_teacheraward (teacher_name, award_name, score) VALUES (%s,%s,%s)",
        rows,
    )
    print(f"[teacher_awards] 导入 {len(rows)} 条")
    return len(rows)


def import_teacher_research(cur):
    f = DATA_DIR / "Teacher_research.csv"
    if not f.exists():
        print("[Teacher_research] 文件不存在，跳过")
        return 0
    rows = []
    with open(f, "r", encoding="gbk", errors="replace") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            name = r.get("姓名", "").strip()
            if not name:
                continue
            count = 0
            for col in ["科研项目_1", "科研项目_2", "科研项目_3", "科研项目_4", "科研项目_5"]:
                try:
                    count += int(float(r.get(col, 0) or 0))
                except (ValueError, TypeError):
                    pass
            score = float(r.get("科研项目总分", 0) or 0)
            rows.append((name[:100], count, score))

    cur.execute("DELETE FROM api_teacherresearch")
    cur.executemany(
        "INSERT INTO api_teacherresearch (teacher_name, project_count, research_score) VALUES (%s,%s,%s)",
        rows,
    )
    print(f"[Teacher_research] 导入 {len(rows)} 条")
    return len(rows)


def import_teaching(cur):
    """从教学系统 SQLite 导入真实课程/教师/成绩数据。

    源库: 教学系统/教学系统/backend/teaching_system_backend/db.sqlite3
    """
    import sqlite3

    db = REPO_ROOT / "教学系统" / "教学系统" / "backend" / "teaching_system_backend" / "db.sqlite3"
    if not db.exists():
        print("[Teaching] 源库不存在，跳过")
        return 0
    con = sqlite3.connect(str(db))
    sc = con.cursor()
    total = 0

    # 课程
    rows = []
    for r in sc.execute("SELECT code, name, credit, hours, course_type FROM course_info"):
        rows.append((r[0], r[1], float(r[2] or 0), int(r[3] or 0), r[4]))
    cur.execute("DELETE FROM api_teachingcourse")
    cur.executemany(
        "INSERT INTO api_teachingcourse (course_code, course_name, credit, hours, course_type) VALUES (%s,%s,%s,%s,%s)",
        rows,
    )
    print(f"[Teaching-Course] 导入 {len(rows)} 条")
    total += len(rows)

    # 教师
    rows = []
    for r in sc.execute("SELECT teacher_no, name, gender, title FROM teacher_info"):
        rows.append((r[0], r[1], r[2], r[3]))
    cur.execute("DELETE FROM api_teachingteacher")
    cur.executemany(
        "INSERT INTO api_teachingteacher (teacher_no, teacher_name, gender, title) VALUES (%s,%s,%s,%s)",
        rows,
    )
    print(f"[Teaching-Teacher] 导入 {len(rows)} 条")
    total += len(rows)

    # 成绩（关联课程名，便于聚合）
    course_map = {}
    for r in sc.execute("SELECT id, code, name FROM course_info"):
        course_map[r[0]] = (r[1], r[2])
    rows = []
    for r in sc.execute("SELECT course_id, grade_type, score, semester_id FROM grade_info"):
        code, name = course_map.get(r[0], ("", ""))
        rows.append((code, name, r[1], float(r[2] or 0), int(r[3] or 0)))
    cur.execute("DELETE FROM api_teachinggrade")
    cur.executemany(
        "INSERT INTO api_teachinggrade (course_code, course_name, grade_type, score, semester_id) VALUES (%s,%s,%s,%s,%s)",
        rows,
    )
    print(f"[Teaching-Grade] 导入 {len(rows)} 条")
    total += len(rows)

    con.close()
    return total


def main():
    print("=== 真实数据批量导入 zhhengguan_research ===")
    conn = get_conn()
    cur = conn.cursor()

    ensure_tables(cur)
    print("新表创建完毕")

    total = 0
    total += import_cnki(cur)
    total += import_guanwang(cur)
    total += import_score_result(cur)
    total += import_teacher_papers(cur)
    total += import_teacher_awards(cur)
    total += import_teacher_research(cur)
    total += import_teaching(cur)

    cur.close()
    conn.close()
    print(f"=== 全部完成，共导入 {total} 条真实数据 ===")


if __name__ == "__main__":
    main()
