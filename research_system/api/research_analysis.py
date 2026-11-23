
import re
from collections import Counter

STOP_PHRASES = {
    '研究','分析','机制','路径','模式','视角','背景','体系','问题','发展','建设','实践',
    '年度','基于','面向','我国','中国','新时代','探索','评价','评估','影响','对策','创新',
}

DOMAIN_TERMS = [
    '数字政府','数字治理','区块链','人工智能','大数据','智慧城市','公共政策','政策执行',
    '绩效评估','社区治理','基层治理','应急管理','公共安全','公共服务','社会保障','乡村振兴',
    '政府改革','行政管理','营商环境','共同富裕','国家治理','治理现代化','政治思想','比较政治',
    '政治制度','政党政治','党的建设','民主治理','全过程人民民主','法治','政治参与','国家建构',
    '全球治理','国际组织','地缘政治','国际安全','区域国别','中美关系','大国关系','战略竞争',
    '国际秩序','一带一路','区域合作','多边合作','气候治理','能源安全','海洋治理','公共卫生',
    '马克思主义','中国特色社会主义','中国式现代化','意识形态','理论创新','文化自信','制度优势',
]

COUNTRY_REGION_RULES = [
    ('美国','北美'),('中美','北美'),('加拿大','北美'),
    ('墨西哥','拉美'),('巴西','拉美'),('拉美','拉美'),
    ('英国','欧洲'),('法国','欧洲'),('德国','欧洲'),('欧盟','欧洲'),('欧洲','欧洲'),
    ('日本','亚洲'),('韩国','亚洲'),('东亚','亚洲'),('东南亚','亚洲'),('印度','亚洲'),('亚洲','亚洲'),
    ('中东','亚洲'),('俄罗斯','欧洲'),('非洲','非洲'),('澳大利亚','大洋洲'),('大洋洲','大洋洲'),
]

DIRECTION_RULES = {
    '科学社会主义系': [
        ('中国特色社会主义',['中国特色社会主义','社会主义']),
        ('国家治理与现代化',['国家治理','治理现代化','中国式现代化']),
        ('党的建设与政党治理',['党建','党的建设','政党治理','政党']),
        ('共同富裕与社会发展',['共同富裕','社会发展','民生']),
        ('马克思主义理论',['马克思主义','理论创新','意识形态']),
    ],
    '政治学系': [
        ('政治思想与理论',['政治思想','思想','理论']),
        ('比较政治与制度',['比较政治','政治制度','制度','政体']),
        ('政党政治',['政党','党建']),
        ('民主与治理',['民主','治理','全过程人民民主']),
        ('公共政策与智库',['政策','智库','咨询']),
    ],
    '国际政治系': [
        ('地缘政治与区域格局',['地缘政治','地缘','区域','格局']),
        ('大国关系与战略竞争',['大国','战略竞争','中美','博弈']),
        ('全球治理与国际组织',['全球治理','国际组织','多边']),
        ('区域国别研究',['区域国别','国别','东亚','欧洲','非洲','中东','东南亚']),
        ('国际安全',['国际安全','安全','防务','冲突','军备']),
    ],
    '公共管理系': [
        ('数字治理',['数字政府','数字治理','大数据','人工智能','智慧城市']),
        ('公共政策',['公共政策','政策执行','政策','评估']),
        ('社区与基层治理',['社区治理','基层治理','社区','基层']),
        ('应急与风险治理',['应急管理','公共安全','风险治理','应急']),
        ('公共服务与社会保障',['公共服务','社会保障','民生']),
        ('政府改革与行政管理',['政府改革','行政管理','营商环境','行政改革']),
    ],
}

def clean_title(text):
    text = (text or '').strip()
    text = re.sub(r'[\s《》“”"\'（）()【】\[\]：:；;，,。.!！?？、/\\\-—_]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def infer_keywords(text, limit=8):
    clean = clean_title(text)
    found = []
    for term in DOMAIN_TERMS:
        if term in clean and term not in found:
            found.append(term)

    chunks = re.split(r'[ 与和及的]', clean)
    for chunk in chunks:
        chunk = chunk.strip()
        chunk = re.sub(r'^(基于|面向|关于|我国|中国)', '', chunk)
        chunk = re.sub(r'(研究|分析|机制|路径|模式|体系|建设|实践|评价|评估|问题)$', '', chunk)
        if 2 <= len(chunk) <= 10 and chunk not in STOP_PHRASES and chunk not in found:
            found.append(chunk)

    return found[:limit]

def infer_direction(dept_name, text):
    rules = DIRECTION_RULES.get(dept_name, [])
    scores = []
    for label, keywords in rules:
        score = sum(1 for keyword in keywords if keyword in (text or ''))
        if score:
            scores.append((score, label))
    scores.sort(key=lambda x: (-x[0], x[1]))
    return scores[0][1] if scores else ''

def infer_geo(text):
    text = text or ''
    countries = []
    regions = []
    for token, region in COUNTRY_REGION_RULES:
        if token in text:
            if token not in {'北美','拉美','欧洲','亚洲','非洲','大洋洲','东亚','东南亚','中东'}:
                countries.append(token)
            regions.append(region)
    country = '、'.join(dict.fromkeys(countries))
    region = regions[0] if regions else ''
    return country, region

def keyword_cloud(rows, limit=28):
    counter = Counter()
    for row in rows:
        raw = getattr(row, 'keywords', '') or ''
        words = [w.strip() for w in raw.split('；') if w.strip()]
        if not words:
            words = infer_keywords(getattr(row, 'project_name', '') or getattr(row, 'title', ''))
        counter.update(words)
    return [{'name': name, 'value': value} for name, value in counter.most_common(limit)]

def direction_counts(rows, labels):
    c = Counter()
    for row in rows:
        direction = (getattr(row, 'research_direction', '') or '').strip()
        if direction:
            c[direction] += 1
    return [c.get(label, 0) for label in labels]

def geo_counts(rows):
    c = Counter()
    for row in rows:
        region = (getattr(row, 'region', '') or '').strip()
        if region:
            c[region] += 1
    regions = ['亚洲','欧洲','北美','拉美','非洲','大洋洲']
    return regions, [c.get(r, 0) for r in regions]
