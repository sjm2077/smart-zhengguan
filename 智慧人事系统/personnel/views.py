"""
智慧人事系统 - 核心数据处理视图
从 Excel 读取 20 张工作表，按工号关联聚合为 JSON
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from django.http import JsonResponse
import openpyxl


# ========== Excel 文件路径 ==========
BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / '人事平台虚拟数据.xlsx'

# ========== 全局业务常量 ==========
# 默认晋升年份基准（与前端 / Node 后端保持一致）
DEFAULT_PROMO_START_YEAR = 2020
DEFAULT_PROMO_END_YEAR = 2025


# ========== Excel 读取 ==========
def load_workbook():
    """加载 Excel 工作簿"""
    try:
        return openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    except Exception as e:
        raise RuntimeError(f'读取 Excel 失败: {e}\n路径: {EXCEL_PATH}')


def read_sheet(wb, name):
    """读取工作表，返回字典列表"""
    if name not in wb.sheetnames:
        return []
    ws = wb[name]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h) if h is not None else '' for h in rows[0]]
    data = []
    for row in rows[1:]:
        record = {}
        for i, h in enumerate(headers):
            record[h] = row[i] if i < len(row) else ''
        data.append(record)
    return data


# ========== 日期解析 ==========
def parse_date(val):
    """解析日期值，统一返回 'YYYY-MM-DD' 字符串"""
    if not val:
        return ''
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    if isinstance(val, (int, float)):
        try:
            base = datetime(1899, 12, 30)
            return (base + timedelta(days=int(val))).strftime('%Y-%m-%d')
        except Exception:
            return str(val).strip()
    return str(val).strip()


# ========== 数据聚合工具 ==========
def group_by(arr, key='工号'):
    """按 key 分组，返回 { key值: [记录列表] }"""
    m = {}
    for r in arr:
        k = r.get(key)
        if not k:
            continue
        m.setdefault(k, []).append(r)
    return m


def _as_date_timestamp(val):
    """将值解析为日期时间戳，用于多条记录取最新；失败返回 None"""
    if not val:
        return None
    if isinstance(val, datetime):
        return val.timestamp()
    if isinstance(val, (int, float)):
        try:
            return (datetime(1899, 12, 30) + timedelta(days=int(val))).timestamp()
        except Exception:
            return None
    s = str(val).strip()
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    return None


def _latest_date_score(record, date_fields):
    """返回记录在 date_fields 中可解析出的最大日期时间戳，无则为 None"""
    best = None
    for f in date_fields:
        ts = _as_date_timestamp(record.get(f))
        if ts is not None and (best is None or ts > best):
            best = ts
    return best


def latest_map(arr, key='工号', date_fields=()):
    """按 key 分组，对同一 key 的多条记录取最新有效记录（按日期比较）。

    规则：
    - 提供了 date_fields 时，保留日期最新的记录；
    - 未提供 date_fields 或均无法解析出日期时，保留第一条（与原 single_map 一致）。
    """
    m = {}
    for r in arr:
        k = r.get(key)
        if not k:
            continue
        if k not in m:
            m[k] = r
            continue
        cur = _latest_date_score(m[k], date_fields)
        new = _latest_date_score(r, date_fields)
        # 仅当新记录日期确凿更新时才替换；两者均无日期时保持第一条
        if new is not None and (cur is None or new > cur):
            m[k] = r
    return m


def safe_float(val):
    """安全转为浮点数"""
    if val is None:
        return 0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0


# ========== 辅助：构建某人的子表数据 ==========
def build_education_list(edu_map, id_):
    return [
        {
            'degree': e.get('学历/学位', ''),
            'school': e.get('毕业院校', ''),
            'major': e.get('专业', ''),
            'start': parse_date(e.get('入学日期')),
            'end': parse_date(e.get('毕业日期')),
        }
        for e in edu_map.get(id_, [])
    ]


def build_work_list(work_map, id_):
    return [
        {
            'company': w.get('单位', ''),
            'position': w.get('职务', ''),
            'start': parse_date(w.get('开始日期')),
            'end': parse_date(w.get('结束日期')),
        }
        for w in work_map.get(id_, [])
    ]


def build_family_members(family_map, id_):
    return [
        {
            'name': f.get('成员姓名', ''),
            'relation': f.get('关系', ''),
            'workplace': f.get('工作单位', ''),
            'phone': f.get('联系方式', ''),
        }
        for f in family_map.get(id_, [])
    ]


def build_assessments(assess_map, id_):
    return [
        {'year': str(a.get('年度', '')), 'result': a.get('考核结果', '')}
        for a in assess_map.get(id_, [])
    ]


def build_transfers(transfer_map, id_):
    return [
        {
            'fromDept': t.get('原部门', ''),
            'toDept': t.get('新部门', ''),
            'date': parse_date(t.get('调动日期')),
        }
        for t in transfer_map.get(id_, [])
    ]


def build_trainings(training_map, id_):
    return [
        {
            'name': t.get('培训名称', ''),
            'date': parse_date(t.get('时间')),
            'location': t.get('地点', ''),
        }
        for t in training_map.get(id_, [])
    ]


def build_honors(honor_map, id_):
    return [
        {
            'name': h.get('称号名称', ''),
            'grantor': h.get('授予单位', ''),
            'date': parse_date(h.get('授予日期')),
        }
        for h in honor_map.get(id_, [])
    ]


def build_social(social_map, id_):
    return [
        {'org': sp.get('组织名称', ''), 'title': sp.get('职务', '')}
        for sp in social_map.get(id_, [])
    ]


def build_promotion_history(promo_map, id_):
    """构建晋升历史"""
    promo_records = promo_map.get(id_, [])
    promo_by_year = {}
    for pr in promo_records:
        year_str = str(pr.get('年份', ''))
        try:
            year = int(float(year_str))
        except (ValueError, TypeError):
            continue
        prob_str = str(pr.get('晋升概率（实际/预测）', ''))
        if '实际' in prob_str:
            promo_by_year[year] = 1.0
        elif '预测' in prob_str:
            try:
                promo_by_year[year] = float(prob_str.replace('%', '')) / 100
            except ValueError:
                pass

    promo_keys = sorted(promo_by_year.keys())
    if promo_keys:
        min_y, max_y = promo_keys[0], promo_keys[-1]
        history = [{'year': y, 'prob': promo_by_year.get(y, 0)}
                   for y in range(min_y, max_y + 1)]
    else:
        history = [{'year': y, 'prob': 0}
                   for y in range(DEFAULT_PROMO_START_YEAR, DEFAULT_PROMO_END_YEAR + 1)]

    prob = history[-1]['prob'] if history else 0
    return history, prob


# ========== 数据缓存（P-01） ==========
_DATA_CACHE = {'data': None, 'mtime': None, 'json': None}


def get_personnel_data_cached():
    """返回缓存的人事数据；Excel 文件修改时间变化时自动重载"""
    mtime = EXCEL_PATH.stat().st_mtime
    if _DATA_CACHE['data'] is None or _DATA_CACHE['mtime'] != mtime:
        _DATA_CACHE['data'] = build_personnel_data()
        _DATA_CACHE['json'] = json.dumps(_DATA_CACHE['data'], ensure_ascii=False)
        _DATA_CACHE['mtime'] = mtime
    return _DATA_CACHE


def calc_etag(json_str):
    """基于序列化内容生成 ETag（P-02）"""
    return '"' + hashlib.md5(json_str.encode('utf-8')).hexdigest() + '"'


# ========== 主数据构建 ==========
def build_personnel_data():
    """构建完整的人事数据 JSON（原 server.js 的 Python 翻译）"""
    wb = load_workbook()

    main_data = read_sheet(wb, '教职工主表')
    education = read_sheet(wb, '学习经历')
    work = read_sheet(wb, '工作经历')
    family = read_sheet(wb, '家庭成员')
    assessments = read_sheet(wb, '年度考核')
    transfers = read_sheet(wb, '校内调动')
    staffing = read_sheet(wb, '编制记录')
    positions = read_sheet(wb, '岗位信息')
    party_pos = read_sheet(wb, '党政职务')
    prof_titles = read_sheet(wb, '专业技术职务')
    skills = read_sheet(wb, '工勤技能')
    dual = read_sheet(wb, '双聘信息')
    abroad = read_sheet(wb, '公派出国')
    teacher_certs = read_sheet(wb, '教师资格证')
    trainings = read_sheet(wb, '培训记录')
    honors = read_sheet(wb, '荣誉称号')
    social = read_sheet(wb, '社会兼职')
    contacts = read_sheet(wb, '联系方式')
    perf_scores = read_sheet(wb, '绩效得分')
    promo_history = read_sheet(wb, '晋升历史')

    edu_map = group_by(education)
    work_map = group_by(work)
    family_map = group_by(family)
    assess_map = group_by(assessments)
    transfer_map = group_by(transfers)
    training_map = group_by(trainings)
    honor_map = group_by(honors)
    social_map = group_by(social)
    perf_map = group_by(perf_scores)
    promo_map = group_by(promo_history)

    st_map = latest_map(staffing, date_fields=('入编日期',))
    pos_map = latest_map(positions, date_fields=('聘用日期',))
    pp_map = latest_map(party_pos, date_fields=('任职开始日期',))
    pt_map = latest_map(prof_titles, date_fields=('获得日期',))
    sk_map = latest_map(skills)  # 工勤技能无日期字段，取第一条
    du_map = latest_map(dual, date_fields=('开始日期',))
    ab_map = latest_map(abroad)  # 起止时间为区间字符串，取第一条
    tc_map = latest_map(teacher_certs, date_fields=('颁发日期',))
    ct_map = latest_map(contacts)  # 联系方式无日期字段，取第一条

    personnel = []
    for row in main_data:
        id_ = row.get('工号', '')
        name = row.get('姓名', '')

        perf_records = sorted(
            perf_map.get(id_, []),
            key=lambda x: str(x.get('年份', '')),
            reverse=True,
        )
        latest_perf = perf_records[0] if perf_records else {}

        promotion_history, promotion_probability = build_promotion_history(promo_map, id_)
        # 统一退休判定：以「离退休状态」字段为主，退休/离休视为已退休
        retire_status = str(row.get('离退休状态', '')).strip()
        is_retired = retire_status in ('退休', '离休')
        retire_date = parse_date(row.get('退休日期'))

        personnel.append({
            'id': id_,
            'name': name,
            'gender': row.get('性别', ''),
            'birthdate': parse_date(row.get('出生日期')),
            'nation': row.get('民族', ''),
            'nativePlace': row.get('籍贯', ''),
            'idCard': row.get('身份证号', ''),
            'politicalStatus': row.get('政治面貌', '群众'),
            'partyJoinDate': parse_date(row.get('入党时间')),
            'partyBranch': row.get('所属党支部', ''),
            'educationList': build_education_list(edu_map, id_),
            'workList': build_work_list(work_map, id_),
            'familyMembers': build_family_members(family_map, id_),
            'annualAssessments': build_assessments(assess_map, id_),
            'internalTransfers': build_transfers(transfer_map, id_),
            'retireInfo': {
                'isRetired': is_retired,
                'retireDate': retire_date,
            },
            'staffingType': {
                'type': st_map.get(id_, {}).get('编制类型', ''),
                'entryDate': parse_date(st_map.get(id_, {}).get('入编日期')),
            },
            'positionInfo': {
                'title': pos_map.get(id_, {}).get('岗位名称', ''),
                'level': pos_map.get(id_, {}).get('岗位等级', ''),
                'hireDate': parse_date(pos_map.get(id_, {}).get('聘用日期')),
            },
            'partyPosition': {
                'title': pp_map.get(id_, {}).get('职务名称', ''),
                'dept': pp_map.get(id_, {}).get('任职部门', ''),
                'startDate': parse_date(pp_map.get(id_, {}).get('任职开始日期')),
            },
            'professionalTitle': {
                'title': pt_map.get(id_, {}).get('职称', ''),
                'major': pt_map.get(id_, {}).get('专业', ''),
                'obtainDate': parse_date(pt_map.get(id_, {}).get('获得日期')),
            },
            'skillLevel': {
                'level': sk_map.get(id_, {}).get('技能等级', ''),
                'trade': sk_map.get(id_, {}).get('工种', ''),
                'cert': sk_map.get(id_, {}).get('证书编号', ''),
            },
            'dualEmployment': {
                'unit': du_map.get(id_, {}).get('双聘单位', ''),
                'position': du_map.get(id_, {}).get('岗位', ''),
                'startDate': parse_date(du_map.get(id_, {}).get('开始日期')),
            },
            'abroadInfo': {
                'country': ab_map.get(id_, {}).get('国家', ''),
                'institution': ab_map.get(id_, {}).get('访学单位', ''),
                'period': ab_map.get(id_, {}).get('起止时间', ''),
            },
            'teacherCert': {
                'type': tc_map.get(id_, {}).get('资格种类', ''),
                'subject': tc_map.get(id_, {}).get('学科', ''),
                'issueDate': parse_date(tc_map.get(id_, {}).get('颁发日期')),
            },
            'trainings': build_trainings(training_map, id_),
            'honors': build_honors(honor_map, id_),
            'socialPositions': build_social(social_map, id_),
            'contact': {
                'phone': ct_map.get(id_, {}).get('手机', ''),
                'email': ct_map.get(id_, {}).get('邮箱', ''),
                'officePhone': ct_map.get(id_, {}).get('办公电话', ''),
                'address': ct_map.get(id_, {}).get('地址', ''),
            },
            'performanceScore': safe_float(latest_perf.get('总分')),
            'teachingScore': safe_float(latest_perf.get('教学得分')),
            'researchScore': safe_float(latest_perf.get('科研得分')),
            'serviceScore': safe_float(latest_perf.get('服务得分')),
            'promotionProbability': promotion_probability,
            'promotionHistory': promotion_history,
        })

    return personnel



# ========== API 视图 ==========
def personnel_api(request):
    """GET /api/personnel — 返回所有人事数据的 JSON（带缓存与 ETag）"""
    try:
        cache = get_personnel_data_cached()
        etag = calc_etag(cache['json'])
        if_none_match = request.headers.get('If-None-Match')
        response = JsonResponse(cache['json'], safe=False)
        response['Cache-Control'] = 'no-cache'
        response['ETag'] = etag
        if if_none_match == etag:
            response.status_code = 304
            return response
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

