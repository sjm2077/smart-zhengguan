import csv
import json
import re
import zipfile
from html import unescape
from io import StringIO
from pathlib import Path
from xml.etree import ElementTree

from django.conf import settings

from apps.graduate.models import ModuleCode, ModuleNotice


SUPPORTED_TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".json", ".csv", ".html", ".htm", ".docx"}
DEFAULT_TOP_K = 4
MAX_TEXT_LENGTH = 12000
MAX_SNIPPET_LENGTH = 180
MIN_EFFECTIVE_TEXT_LENGTH = 50

DOMAIN_KEYWORDS = [
    "预警",
    "学业",
    "培养",
    "课程",
    "奖学金",
    "助学金",
    "奖助",
    "学籍",
    "就业",
    "毕业",
    "答辩",
    "导师",
    "考核",
    "心理",
    "出勤",
    "科研",
]

QUERY_EXPANSION_MAP = {
    "奖助": ["奖学金", "助学金", "评审", "资助"],
    "奖学金": ["奖学金", "评审", "获奖", "学业奖学金"],
    "助学金": ["助学金", "资助", "发放"],
    "学籍": ["学籍", "休学", "保留学籍", "复学"],
    "预警": ["预警", "学业", "考核", "培养"],
    "课程": ["课程", "教学", "成绩", "不及格"],
    "培养": ["培养", "培养计划", "考核", "中期"],
    "答辩": ["答辩", "毕业", "学位", "论文"],
    "就业": ["就业", "签约", "派遣", "毕业去向"],
}

POLICY_QUERY_KEYWORDS = [
    "优秀毕业生",
    "评优",
    "评选",
    "资格",
    "条件",
    "标准",
    "要求",
    "材料",
    "流程",
    "办法",
    "规定",
]

POLICY_QUERY_EXPANSION_MAP = {
    "优秀毕业生": ["优秀毕业生", "毕业生", "评选", "评优"],
    "评优": ["评优", "评选", "评审", "推荐"],
    "评选": ["评选", "评审", "推荐", "办法"],
    "资格": ["资格", "条件", "要求", "标准"],
    "条件": ["条件", "要求", "标准", "资格"],
    "标准": ["标准", "条件", "要求", "评审"],
    "要求": ["要求", "条件", "标准", "规定"],
    "材料": ["材料", "提交", "审核", "流程"],
    "流程": ["流程", "申报", "审核", "办理"],
    "办法": ["办法", "规定", "评选", "审核"],
    "规定": ["规定", "办法", "要求", "流程"],
}


def retrieve_prediction_knowledge(question, context, top_k=None):
    top_k = int(top_k or getattr(settings, "PREDICTION_KNOWLEDGE_TOP_K", DEFAULT_TOP_K))
    query_terms = build_query_terms(question, context)
    if not query_terms:
        return []

    candidates = []
    candidates.extend(retrieve_local_file_chunks(query_terms))
    candidates.extend(retrieve_module_notices(query_terms))

    unique = []
    unique_by_source = []
    seen = set()
    seen_source = set()
    sorted_candidates = sorted(candidates, key=lambda row: (-row["score"], row["title"], row["section"]))
    for item in sorted_candidates:
        key = (item["title"], item["section"], item["snippet"])
        if key in seen:
            continue
        seen.add(key)
        normalized_item = {
            "title": item["title"],
            "section": item["section"],
            "snippet": item["snippet"],
            "sourceType": item["sourceType"],
            "sourcePath": item["sourcePath"],
            "url": item.get("url", ""),
            "score": round(item["score"], 2),
        }
        source_key = (normalized_item["sourceType"], normalized_item["sourcePath"], normalized_item["title"])
        if source_key not in seen_source:
            seen_source.add(source_key)
            unique_by_source.append(normalized_item)
        else:
            unique.append(normalized_item)
    results = (unique_by_source + unique)[:top_k]
    return results


def build_query_terms(question, context):
    raw_terms = []
    cleaned_question = normalize_space(str(question or ""))
    if cleaned_question:
        raw_terms.append(cleaned_question)
        raw_terms.extend(re.split(r"[，。；：、？！,\s]+", cleaned_question))

    student = context.get("student") or {}
    prediction = context.get("prediction") or {}
    raw_terms.extend([
        student.get("major", ""),
        student.get("grade", ""),
        student.get("college", ""),
        prediction.get("riskField", ""),
        prediction.get("riskCategory", ""),
        prediction.get("riskLevel", ""),
    ])

    for keyword in DOMAIN_KEYWORDS:
        if keyword in cleaned_question:
            raw_terms.append(keyword)
            raw_terms.extend(QUERY_EXPANSION_MAP.get(keyword, []))

    for keyword in POLICY_QUERY_KEYWORDS:
        if keyword in cleaned_question:
            raw_terms.append(keyword)
            raw_terms.extend(POLICY_QUERY_EXPANSION_MAP.get(keyword, []))

    normalized = []
    seen = set()
    for term in raw_terms:
        text = normalize_space(str(term or ""))
        if len(text) < 2:
            continue
        if text in seen:
            continue
        seen.add(text)
        normalized.append(text[:40])
    return normalized


def retrieve_local_file_chunks(query_terms):
    results = []
    for root in resolve_knowledge_dirs():
        if not root.exists() or not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.name.lower() == "readme.md":
                continue
            if path.suffix.lower() not in SUPPORTED_TEXT_SUFFIXES:
                continue
            text = extract_text_from_file(path)
            if not text or len(normalize_space(text)) < MIN_EFFECTIVE_TEXT_LENGTH:
                continue
            for index, chunk in enumerate(split_text_into_chunks(text)):
                score = score_text(chunk, path.stem, query_terms)
                if score <= 0:
                    continue
                results.append({
                    "title": path.stem,
                    "section": f"chunk-{index + 1}",
                    "snippet": build_snippet(chunk, query_terms),
                    "sourceType": "local_file",
                    "sourcePath": str(path),
                    "url": "",
                    "score": score,
                })
    return results


def retrieve_module_notices(query_terms):
    results = []
    notices = ModuleNotice.objects.filter(module__in=[
        ModuleCode.INTELLIGENT_PREDICTION,
        ModuleCode.TRAINING,
        ModuleCode.DEGREE,
        ModuleCode.DEGREE_DEFENSE,
        ModuleCode.SCHOLARSHIP,
        ModuleCode.EMPLOYMENT,
        ModuleCode.HOME,
    ])
    for notice in notices:
        text = normalize_space("\n".join([
            notice.title,
            notice.content,
            notice.url,
        ]))
        if not text:
            continue
        score = score_text(text, notice.title, query_terms)
        if score <= 0:
            continue
        results.append({
            "title": notice.title,
            "section": notice.module,
            "snippet": build_snippet(text, query_terms),
            "sourceType": "module_notice",
            "sourcePath": f"ModuleNotice:{notice.id}",
            "url": notice.url or "",
            "score": score,
        })
    return results


def resolve_knowledge_dirs():
    configured = getattr(settings, "PREDICTION_KNOWLEDGE_DIRS", [])
    if not configured:
        configured = ["knowledge/prediction", "../研究生文件规定"]

    configured = list(configured) + ["../研究生文件规定_解析版"]
    resolved = []
    for item in configured:
        raw_path = Path(str(item))
        path = raw_path if raw_path.is_absolute() else (settings.BASE_DIR / raw_path).resolve()
        resolved.append(path)
    return resolved


def extract_text_from_file(path):
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md", ".markdown", ".html", ".htm"}:
            return read_text_with_fallback(path)
        if suffix == ".json":
            payload = json.loads(read_text_with_fallback(path) or "{}")
            return normalize_space(json.dumps(payload, ensure_ascii=False, indent=2))
        if suffix == ".csv":
            return csv_file_to_text(path)
        if suffix == ".docx":
            return docx_to_text(path)
    except Exception:
        return ""
    return ""


def read_text_with_fallback(path):
    for encoding in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            return path.read_text(encoding=encoding)[:MAX_TEXT_LENGTH]
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")[:MAX_TEXT_LENGTH]


def csv_file_to_text(path):
    raw_text = read_text_with_fallback(path)
    reader = csv.reader(StringIO(raw_text))
    rows = []
    for index, row in enumerate(reader):
        rows.append(" | ".join(cell.strip() for cell in row if cell.strip()))
        if index >= 30:
            break
    return "\n".join(rows)[:MAX_TEXT_LENGTH]


def docx_to_text(path):
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml_bytes)
    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall(".//w:p", namespaces):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", namespaces)]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)[:MAX_TEXT_LENGTH]


def split_text_into_chunks(text, chunk_size=700, overlap=120):
    cleaned = normalize_space(unescape(text))
    if len(cleaned) <= chunk_size:
        return [cleaned] if cleaned else []

    chunks = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunks.append(cleaned[start:end])
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks


def score_text(text, title, query_terms):
    haystack = normalize_space(f"{title}\n{text}")
    if not haystack:
        return 0

    score = 0
    for term in query_terms:
        if term in title:
            score += 8
        if term in haystack:
            score += 5
        compact = term.replace(" ", "")
        if compact and compact != term and compact in haystack:
            score += 3
    return score


def build_snippet(text, query_terms):
    haystack = normalize_space(unescape(text))
    match_index = -1
    matched_term = ""
    for term in query_terms:
        position = haystack.find(term)
        if position >= 0 and (match_index < 0 or position < match_index):
            match_index = position
            matched_term = term

    if match_index < 0:
        return haystack[:MAX_SNIPPET_LENGTH]

    start = max(0, match_index - 40)
    end = min(len(haystack), match_index + max(len(matched_term), 20) + 120)
    snippet = haystack[start:end]
    return snippet[:MAX_SNIPPET_LENGTH]


def normalize_space(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()
