"""山东大学政治学与公共管理学院官网真实数据爬虫。

采集内容（全部来自官网 https://pspa.sdu.edu.cn 真实页面）：
  1. 全职教师（dept + 职称 + 姓名 + 个人主页）  /jytd/qzjs.htm
  2. 学术成果（成果类别 + 标题 + 发布日期）      /xsky/xscg.htm（自动翻页）
  3. 通知公告（标题 + 发布日期 + 正文）          /tzgg1.htm（自动翻页）
  4. 学院简介权威指标（师资/科研/招生人数）     /xygk/xyjj.htm
  5. 教师详情页（研究方向/简历/项目/课程）       个人主页（站内 + faculty.sdu.edu.cn）

落库：MySQL zhhengguan_research
  api_pspa_teacher / api_pspa_achievement / api_pspa_notice / api_pspa_stat

用法：
  python scripts/crawler_pspa.py --once        # 抓一次
  python scripts/crawler_pspa.py --schedule    # 每 6 小时定时
  python scripts/crawler_pspa.py --once --pages 20
  python scripts/crawler_pspa.py --once --pages 20 --with-detail --teacher-profile   # 全量
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import time
from urllib.parse import urljoin, urlsplit

import pymysql
import requests
from bs4 import BeautifulSoup

BASE = 'https://pspa.sdu.edu.cn'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}
requests.packages.urllib3.disable_warnings()

DB = dict(
    host=os.getenv('IMPORT_DB_HOST', '127.0.0.1'),
    port=int(os.getenv('IMPORT_DB_PORT', '3306')),
    user=os.getenv('IMPORT_DB_USER', 'root'),
    password=os.getenv('IMPORT_DB_PASS', 'root'),
    database=os.getenv('IMPORT_DB_NAME', 'zhhengguan_research'),
    charset='utf8mb4',
    autocommit=True,
)


def fetch(url, retry=3):
    last = None
    for i in range(retry):
        try:
            r = requests.get(url, headers=HEADERS, timeout=25, verify=False)
            ctype = (r.headers.get('Content-Type') or '').lower()
            if 'charset=' in ctype:
                r.encoding = ctype.split('charset=')[-1].split(';')[0].strip()
            else:
                # 学校部分站点不声明 charset，requests 会默认 ISO-8859-1 导致乱码；
                # 先按 UTF-8 严格解码，失败再交给 apparent_encoding
                try:
                    r.content.decode('utf-8')
                    r.encoding = 'utf-8'
                except UnicodeDecodeError:
                    r.encoding = r.apparent_encoding or 'utf-8'
            if r.status_code == 200:
                return r.text
            last = 'HTTP %s' % r.status_code
        except Exception as exc:
            last = str(exc)
        time.sleep(1.5 * (i + 1))
    print('    [WARN] fetch failed: %s (%s)' % (url, last))
    return ''


def clean(text):
    return re.sub(r'\s+', ' ', (text or '').replace('\u3000', ' ')).strip()


def ensure_tables(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_pspa_teacher (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(64) NOT NULL,
            title VARCHAR(32),
            dept VARCHAR(64),
            url VARCHAR(512),
            url_hash VARCHAR(32) UNIQUE,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_title (title),
            INDEX idx_dept (dept)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_pspa_achievement (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(32),
            title VARCHAR(500) NOT NULL,
            publish_date VARCHAR(32),
            url VARCHAR(512),
            url_hash VARCHAR(32) UNIQUE,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_cat (category),
            INDEX idx_date (publish_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_pspa_notice (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            publish_date VARCHAR(32),
            url VARCHAR(512),
            url_hash VARCHAR(32) UNIQUE,
            content MEDIUMTEXT,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_date (publish_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    # 老表升级：补 content 列（供知识库全文检索使用）
    try:
        cur.execute("ALTER TABLE api_pspa_notice ADD COLUMN content MEDIUMTEXT NULL AFTER url_hash")
    except Exception:
        pass
    # 老表升级：教师详情页正文 / 研究方向 / 来源站（供知识库“某老师研究什么”类问题）
    for ddl in (
        "ALTER TABLE api_pspa_teacher ADD COLUMN profile MEDIUMTEXT NULL",
        "ALTER TABLE api_pspa_teacher ADD COLUMN research VARCHAR(300) NULL",
        "ALTER TABLE api_pspa_teacher ADD COLUMN profile_source VARCHAR(32) NULL",
        "ALTER TABLE api_pspa_teacher ADD COLUMN profile_status VARCHAR(48) NULL",
    ):
        try:
            cur.execute(ddl)
        except Exception:
            pass
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_pspa_stat (
            id INT AUTO_INCREMENT PRIMARY KEY,
            stat_key VARCHAR(64) NOT NULL UNIQUE,
            label VARCHAR(128),
            value DECIMAL(18, 2),
            unit VARCHAR(32),
            raw_text VARCHAR(500),
            source_url VARCHAR(512),
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    # 现任领导（职务/姓名/分工），用于登录演示账号与画像页“实名但不冒充”的来源标注
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_pspa_leader (
            id INT AUTO_INCREMENT PRIMARY KEY,
            post VARCHAR(64) NOT NULL,
            name VARCHAR(64) NOT NULL,
            duty VARCHAR(500),
            source_url VARCHAR(512),
            url_hash VARCHAR(32) UNIQUE,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_post (post)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


# ---------------- 0b. 现任领导（官网 /xygk/xrld.htm） ----------------
def crawl_leaders(cur):
    """现任领导表：职务 / 姓名 / 工作分工。

    这张表只用于“角色-公开职责”对照（如登录页的院长账号对应官网院长分工），
    不代表任何人的真实账号或密码。
    """
    url = BASE + '/xygk/xrld.htm'
    html = fetch(url)
    if not html:
        return 0
    soup = BeautifulSoup(html, 'html.parser')
    box = soup.find('div', class_='v_news_content') or soup.find('div', class_='c-content') or soup
    table = box.find('table')
    if table is None:
        return 0

    rows = []
    for tr in table.find_all('tr'):
        cells = [clean(td.get_text(' ', strip=True)) for td in tr.find_all(['td', 'th'])]
        if len(cells) < 3:
            continue
        for start in (0, 3):
            if len(cells) < start + 3:
                continue
            post, name, duty = cells[start], cells[start + 1], cells[start + 2]
            post = re.sub(r'\s+', '', post)
            name = re.sub(r'\s+', '', name)
            if not name or name == '姓名' or len(name) > 20:
                continue
            h = hashlib.md5((post + '|' + name).encode()).hexdigest()
            rows.append((post[:64], name[:64], clean(duty)[:500], url, h))

    if not rows:
        return 0
    # 领导名单是“整页快照”，直接以本次抓取结果为准（表很小，不存在历史累积问题）
    cur.execute("DELETE FROM api_pspa_leader")
    cur.executemany(
        "INSERT INTO api_pspa_leader (post, name, duty, source_url, url_hash) "
        "VALUES (%s,%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE duty=VALUES(duty), fetched_at=CURRENT_TIMESTAMP",
        rows,
    )
    print('  [学院领导] %d 人（来源：/xygk/xrld.htm）' % len(rows))
    return len(rows)


# ---------------- 1. 全职教师 ----------------
def crawl_teachers(cur):
    html = fetch(BASE + '/jytd/qzjs.htm')
    if not html:
        return 0
    soup = BeautifulSoup(html, 'html.parser')
    rows = []

    for box in soup.select('div.box_xs'):
        # 系名：box 文本最前面的“XX系/研究院”，在第一个 zc_box 之前
        dept = ''
        first_zc = box.find('div', class_='zc_box')
        prefix = ''
        if first_zc is not None:
            for node in first_zc.previous_elements:
                txt = getattr(node, 'get_text', None)
                if txt and node.name in ('h1', 'h2', 'h3', 'h4', 'p', 'span', 'div'):
                    prefix = clean(txt())
                    if prefix:
                        break
        if not prefix:
            prefix = clean(box.get_text(' ', strip=True))[:20]
        m = re.match(r'([\u4e00-\u9fa5A-Za-z]{2,20}(?:系|研究院|研究所|中心))', prefix)
        if m:
            dept = m.group(1)

        # 逐个职称区，跟踪当前职称
        current_title = ''
        for zc in box.select('div.zc_box'):
            h2 = zc.find('h2')
            title = clean(h2.get_text()) if h2 else ''
            if title:
                current_title = title
            for a in zc.select('ul.ul_box li a'):
                name = re.sub(r'\s+', '', clean(a.get_text()))
                if not name or len(name) < 2 or len(name) > 20:
                    continue
                href = a.get('href', '')
                url = urljoin(BASE + '/jytd/', href) if href else ''
                h = hashlib.md5((url or (dept + name)).encode()).hexdigest()
                rows.append((name, current_title, dept, url[:512], h))

    # 去重（同一教师可能出现在多个栏目）
    seen, uniq = set(), []
    for r in rows:
        key = (r[0], r[1], r[2])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    # 用 upsert 而非 DELETE：教师详情页正文（profile）很贵，重跑列表时不能把它冲掉
    cur.executemany(
        "INSERT INTO api_pspa_teacher (name, title, dept, url, url_hash) VALUES (%s,%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE name=VALUES(name), title=VALUES(title), "
        "dept=VALUES(dept), url=VALUES(url), fetched_at=CURRENT_TIMESTAMP",
        uniq,
    )
    print('  [教师] %d 人（%d 个系/机构）' % (len(uniq), len({r[2] for r in uniq})))
    return len(uniq)


# ---------------- 1b. 教师详情页（研究方向/简历） ----------------
RESEARCH_RULES = [
    r'研究方向\s*[:：]?\s*([^。；;]{2,120})',
    r'主要研究领域\s*[:：]?\s*([^。；;]{2,120})',
    r'研究领域\s*(?:为|是)?\s*[:：]?\s*([^。；;]{2,120})',
    r'主要从事\s*([^。；;]{2,120})',
    r'学科\s*[:：]\s*([^。；;]{2,120})',
]


def extract_teacher_text(url, html, name):
    """从教师详情页取正文，返回 (正文, 来源, 失败原因)。

    教师页有三套模板：
    - 学院官网 pspa.sdu.edu.cn：正文在 div.v_news_content / div.c-content
    - 学校教师主页 faculty.sdu.edu.cn：正文在 div.dft-main / div.p_right / div.t_main 等
    - 其他 *.sdu.edu.cn 站点（如 faculty-cms）：用页面标题确认本人后取最长正文
    取不到时返回空正文 + 原因，便于调用方如实统计而不是静默跳过。
    """
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()

    title = clean(soup.title.get_text()) if soup.title else ''
    if ('系统提示' in title or '统一身份' in title or '登录' in title) and len(
            soup.get_text(strip=True)) < 300:
        return '', '', '需登录'

    nospace = re.sub(r'\s+', '', name)
    title_has_name = name in title or nospace in re.sub(r'\s+', '', title)

    CHROME = ('nav', 'menu', 'foot', 'head', 'crumb', 'sidebar', 'banner', 'topbar',
              'logo', 'search', 'share', 'related', 'copyright')

    def is_chrome(el):
        cls = ' '.join(el.get('class') or []).lower()
        eid = (el.get('id') or '').lower()
        return any(k in cls or k in eid for k in CHROME)

    def is_junk(text):
        return text.startswith('首页') or '欢迎访问山东大学政治学与公共管理学院' in text[:80]

    def has_name(text):
        return name in text or nospace in re.sub(r'\s+', '', text)

    if 'faculty.sdu.edu.cn' in url:
        selectors = ('div.p_right', 'div.dft-main', 'div.t_main', 'div.ContentBox',
                     'div.content', 'div.juzhong', 'div.main', 'div.t_block')
    else:
        selectors = ('div.v_news_content', 'div.c-content', 'div.content',
                     'div.article-content', 'div#content', 'div.floor')

    cands = []
    # 第一轮：正文里出现本人姓名，最可靠
    for sel in selectors:
        for el in soup.select(sel):
            if is_chrome(el):
                continue
            text = clean(el.get_text(' ', strip=True))
            if len(text) >= 50 and not is_junk(text) and has_name(text):
                cands.append(text)

    # 第二轮：页面标题确认是本人页，但正文面板不含姓名（如“个人简介暂无内容”）
    if not cands and title_has_name:
        for sel in selectors:
            for el in soup.select(sel):
                if is_chrome(el):
                    continue
                text = clean(el.get_text(' ', strip=True))
                if len(text) >= 60 and not is_junk(text):
                    cands.append(text)

    # 第三轮：其他子站模板差异大，取页内最长的非导航正文
    if not cands and title_has_name:
        for el in soup.find_all(['div', 'article', 'section']):
            if is_chrome(el):
                continue
            text = clean(el.get_text(' ', strip=True))
            if len(text) >= 120 and not is_junk(text):
                cands.append(text)

    if not cands:
        return '', '', '页面无正文'

    # 长文本优先；被长文本包含的短文本直接丢弃，避免同一段内容重复入库
    parts = []
    for text in sorted(cands, key=len, reverse=True):
        if any(text in p or p in text for p in parts):
            continue
        parts.append(text)
    text = re.sub(r'\s*上一篇[:：].*$', '', clean(' '.join(parts)))
    if len(text) < 50:
        return '', '', '页面无正文'

    source = '教师主页' if 'faculty.sdu.edu.cn' in url else '学院官网'
    return text[:200000], source, ''


SECTION_BREAK = re.compile(
    r'(?:[一二三四五六七八九十]+、|Research Focus|Social Affiliations|Personal Information|'
    r'个人信息|个人简介|基本信息|研究方向|主要研究领域|研究领域|主要从事|学科|'
    r'主要代表作品|代表性|主持承担|主要承担|主要科研项目|科研项目|论文成果|论文|'
    r'主要开设课程|主讲课程|授课信息|教育经历|工作经历|学术兼职|社会兼职|获奖信息|'
    r'团队成员|办公地点|电子邮箱|联系方式|访问次数|扫描关注|同专业博导|同专业硕导|'
    r'职称|性别|学历|学位|毕业院校|【)'
)


def extract_research(text):
    for pattern in RESEARCH_RULES:
        m = re.search(pattern, text)
        if m:
            value = clean(m.group(1))
            # 遇到下一个章节标题/字段就截断（官网正文常写成“四、研究方向 … 五、主讲课程 …”）
            value = SECTION_BREAK.split(value)[0]
            value = clean(value).strip('，,、:：】] 【[')
            if 2 <= len(value) <= 200:
                return value
    return ''


def crawl_teacher_profiles(cur, limit=0, retry_failed=False):
    """补采教师详情页正文（供知识库回答“某老师研究什么方向/主持什么项目”）。

    只抓个人主页链接（学院官网站内 + 学校教师主页 faculty.sdu.edu.cn），
    抓不到正文（外链失效/需登录/页面过短）就如实记下原因，默认不再重抓；
    加 retry_failed=True 可重试之前失败的人（个别老师后续会补上主页）。
    """
    where = "url <> '' AND (profile IS NULL OR profile = '')"
    if retry_failed:
        where += " AND (profile_status IS NULL OR profile_status <> 'ok')"
    else:
        where += " AND profile_status IS NULL"
    cur.execute("SELECT id, name, url FROM api_pspa_teacher WHERE %s ORDER BY id" % where)
    targets = cur.fetchall()
    if limit:
        targets = targets[:limit]
    if not targets:
        print('  [教师详情] 无需补采')
        return 0

    done = 0
    reasons = {}
    for idx, (tid, name, url) in enumerate(targets, 1):
        # 只接受山东大学官方域名（学院官网 / 学校教师主页 / 各研究所子站），外链一律跳过
        host = urlsplit(url or '').netloc.lower()
        if not host.endswith('.sdu.edu.cn'):
            reason = '外链非山大域名'
        else:
            html = fetch(url)
            if not html:
                reason = '抓取失败'
            else:
                text, source, reason = extract_teacher_text(url, html, name)
                if text:
                    cur.execute("UPDATE api_pspa_teacher SET profile = %s, research = %s, "
                                "profile_source = %s, profile_status = 'ok' WHERE id = %s",
                                (text, extract_research(text)[:300], source, tid))
                    done += 1
                    if idx % 10 == 0:
                        print('    [教师详情] %d/%d' % (idx, len(targets)))
                    time.sleep(0.25)
                    continue
        # 采不到就记下原因并落库，下次不再重复抓同一张空页
        reasons[reason] = reasons.get(reason, 0) + 1
        cur.execute("UPDATE api_pspa_teacher SET profile_status = %s WHERE id = %s", (reason, tid))
    cur.execute("SELECT COUNT(*) FROM api_pspa_teacher WHERE profile IS NOT NULL AND profile <> ''")
    total = cur.fetchone()[0]
    detail = '、'.join('%s %d 人' % (k, v) for k, v in reasons.items()) or '无'
    print('  [教师详情] 本次补采 %d 人，库内已有详情 %d 人；未采到：%s' % (done, total, detail))
    return done


# ---------------- 通用列表翻页 ----------------
def crawl_list(start_path, max_pages, parser, label):
    url = BASE + start_path
    visited = set()
    rows = []
    page = 0

    while url and page < max_pages and url not in visited:
        visited.add(url)
        page += 1
        html = fetch(url)
        if not html:
            break
        soup = BeautifulSoup(html, 'html.parser')
        page_rows = parser(soup, url)
        rows.extend(page_rows)
        print('    %s page %d: %d 条' % (label, page, len(page_rows)))

        nxt = None
        for a in soup.find_all('a', href=True):
            if clean(a.get_text()) in ('下页', '下一页'):
                nxt = urljoin(url, a['href'])
                break
        if not nxt or nxt in visited:
            break
        url = nxt
        time.sleep(0.6)

    seen, uniq = set(), []
    for r in rows:
        if r[-1] in seen:
            continue
        seen.add(r[-1])
        uniq.append(r)
    return uniq


def parse_achievements(soup, page_url):
    out = []
    for li in soup.select('div.lm_list li'):
        a = li.find('a', href=True)
        if not a:
            continue
        raw = clean(a.get_text())
        span = li.find('span')
        date = clean(span.get_text()) if span else ''
        m = re.match(r'[【\[]([^】\]]+)[】\]]\s*(.*)', raw)
        category = clean(m.group(1)) if m else ''
        title = clean(m.group(2)) if m else raw
        if not title:
            continue
        url = urljoin(page_url, a['href'])[:512]
        h = hashlib.md5(url.encode()).hexdigest()
        out.append((category[:32], title[:500], date[:32], url, h))
    return out


def parse_notices(soup, page_url):
    out = []
    for li in soup.select('div.lm_list li'):
        a = li.find('a', href=True)
        if not a:
            continue
        title = clean(a.get_text())
        span = li.find('span')
        date = clean(span.get_text()) if span else ''
        if not title:
            continue
        url = urljoin(page_url, a['href'])[:512]
        h = hashlib.md5(url.encode()).hexdigest()
        out.append((title[:500], date[:32], url, h))
    return out


def crawl_achievements(cur, max_pages):
    rows = crawl_list('/xsky/xscg.htm', max_pages, parse_achievements, '学术成果')
    # 用 upsert 累积：翻页数少时不至于把之前抓全的历史记录删掉
    cur.executemany(
        "INSERT INTO api_pspa_achievement (category, title, publish_date, url, url_hash) "
        "VALUES (%s,%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE category=VALUES(category), title=VALUES(title), "
        "publish_date=VALUES(publish_date), url=VALUES(url)",
        rows,
    )
    cur.execute("SELECT COUNT(*) FROM api_pspa_achievement")
    total = cur.fetchone()[0]
    print('  [学术成果] 本次 %d 条，库内累计 %d 条' % (len(rows), total))
    return len(rows)


def crawl_notices(cur, max_pages):
    rows = crawl_list('/tzgg1.htm', max_pages, parse_notices, '通知公告')
    # 用 upsert 而非 DELETE：保留已抓取的正文（content），列表刷新只更新标题/日期
    cur.executemany(
        "INSERT INTO api_pspa_notice (title, publish_date, url, url_hash) VALUES (%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE title=VALUES(title), publish_date=VALUES(publish_date), "
        "url=VALUES(url), fetched_at=CURRENT_TIMESTAMP",
        rows,
    )
    cur.execute("SELECT COUNT(*) FROM api_pspa_notice")
    total = cur.fetchone()[0]
    print('  [通知公告] 本次 %d 条，库内累计 %d 条' % (len(rows), total))
    return len(rows)


def crawl_notice_details(cur, limit=0):
    """抓通知公告正文（供知识库全文检索）。limit=0 表示全量。

    只抓 pspa.sdu.edu.cn 站内页：外站（oa.sdu.edu.cn 统一身份登录页、
    rwsk/mpa/ttc 子站已 404、青岛校区站点）无法匿名取得正文，如实跳过并统计，
    不把登录页当正文写库。
    """
    cur.execute("SELECT id, url FROM api_pspa_notice WHERE content IS NULL OR content = '' ORDER BY id DESC")
    targets = cur.fetchall()
    if limit:
        targets = targets[:limit]
    if not targets:
        print('  [通知正文] 无需补采')
        return 0

    inside = [(i, u) for i, u in targets if (u or '').startswith(BASE)]
    outside = len(targets) - len(inside)

    done = 0
    for idx, (nid, url) in enumerate(inside, 1):
        html = fetch(url)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        # 有的页面正文在附件里，v_news_content 只有一句“请见附件”，此时退回 c-content 取标题/日期/说明
        best = ''
        for sel in ('div.v_news_content', 'div.c-content'):
            el = soup.select_one(sel)
            if el is None:
                continue
            for tag in el.find_all(['script', 'style']):
                tag.decompose()
            text = clean(el.get_text(' ', strip=True))
            if len(text) > len(best):
                best = text
        if len(best) < 40:
            continue
        cur.execute("UPDATE api_pspa_notice SET content = %s WHERE id = %s", (best[:200000], nid))
        done += 1
        if idx % 25 == 0:
            print('    [通知正文] %d/%d' % (idx, len(inside)))
        time.sleep(0.25)
    print('  [通知正文] 补采 %d 篇；跳过 %d 篇（外站/OA 需登录或已失效，正文不可得）' % (done, outside))
    return done


# ---------------- 4. 学院简介权威指标 ----------------
# 官网《学院简介》/xygk/xyjj.htm 里以中文陈述的官方权威数字，
# 是全站唯一“学院自己公布”的口径，用于校准大屏 KPI。
CN_DIGIT = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9}
CN_UNIT = {'十': 10, '百': 100, '千': 1000}


def cn_to_int(text):
    """把「六千」这类中文数字转成整数（仅需支持千以内）。"""
    total, num = 0, 0
    for ch in text:
        if ch in CN_DIGIT:
            num = CN_DIGIT[ch]
        elif ch in CN_UNIT:
            total += (num or 1) * CN_UNIT[ch]
            num = 0
    return total + num


# (stat_key, label, unit, 正则) —— 正则第 1 组必须是数字
PROFILE_RULES = [
    ('teacher_total', '在职教师', '人', r'在职教师\s*(\d+)\s*人'),
    ('teacher_professor', '教授', '人', r'教授\s*(\d+)\s*人'),
    ('teacher_associate', '副教授（副研究员）', '人', r'副教授（副研究员）\s*(\d+)\s*人'),
    ('teacher_lecturer', '讲师（助理研究员）', '人', r'讲师（助理研究员）\s*(\d+)\s*人'),
    ('teacher_postdoc', '全职博士后', '人', r'全职博士后\s*(\d+)\s*人'),
    ('teacher_phd', '具有博士学位', '人', r'(\d+)\s*人具有博士学位'),
    ('teacher_overseas', '海外名校毕业', '人', r'(\d+)\s*人毕业于海外名校'),
    ('supervisor_phd', '博士生导师', '人', r'博士生导师\s*(\d+)\s*人'),
    ('supervisor_master', '硕士生导师', '人', r'硕士生导师\s*(\d+)\s*人'),
    ('paper_total', '近五年发表论文', '篇', r'发表论文\s*(\d+)\s*多?篇'),
    ('paper_ssci', 'SSCI 论文', '篇', r'SSCI\s*论文\s*(\d+)\s*多?篇'),
    ('paper_cssci', 'CSSCI 来源期刊论文', '篇', r'CSSCI\s*来源期刊论文\s*(\d+)\s*余?篇'),
    ('book_total', '出版著作', '部', r'出版著作\s*(\d+)\s*余?部'),
    ('thinktank_report', '智库报告', '篇', r'智库报告\s*(\d+)\s*余?篇'),
    ('project_major', '国家社科重大/教育部重大攻关', '项', r'重大攻关项目\s*(\d+)\s*余?项'),
    ('project_nssf', '国家社科基金各类项目', '项', r'国家社科基金各类项目\s*(\d+)\s*余?项'),
    ('project_nsfc', '国家自然科学基金项目', '项', r'国家自然科学基金项目\s*(\d+)\s*余?项'),
    ('project_ministry', '其他部委各类项目', '项', r'其他部委各类项目\s*(\d+)\s*多?项'),
    ('enroll_undergrad', '每年招收本科生', '人/年', r'每年招收本科生\s*(\d+)\s*人'),
    ('enroll_master', '每年招收学术硕士', '人/年', r'学术硕士研究生\s*(\d+)\s*人'),
    ('enroll_doctor', '每年招收博士', '人/年', r'博士研究生\s*(\d+)\s*人'),
    ('enroll_mpa', '每年招收公共管理专业硕士', '人/年', r'公共管理专业学位硕士研究生\s*(\d+)\s*人'),
    ('enroll_intl', '每年招收全英文项目留学生', '人/年', r'全英文授课项目留学生\s*(\d+)\s*人'),
]


def crawl_profile_stats(cur):
    url = BASE + '/xygk/xyjj.htm'
    html = fetch(url)
    if not html:
        return 0
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.select_one('div.c-content') or soup.select_one('div.lm_list') or soup.body
    text = clean(body.get_text(' ', strip=True))

    rows = []
    for key, label, unit, pattern in PROFILE_RULES:
        m = re.search(pattern, text)
        if not m:
            print('    [MISS] %s' % key)
            continue
        rows.append((key, label, float(m.group(1)), unit, m.group(0)[:500], url))

    # 总项目经费：中文数字「六千余万元」→ 6000 万元
    m = re.search(r'总项目经费([零一二三四五六七八九十百千]+)余?万', text)
    if m:
        rows.append(('fund_total', '近五年科研项目总经费', float(cn_to_int(m.group(1))),
                     '万元', m.group(0)[:500], url))

    cur.executemany(
        "INSERT INTO api_pspa_stat (stat_key, label, value, unit, raw_text, source_url) "
        "VALUES (%s,%s,%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE label=VALUES(label), value=VALUES(value), unit=VALUES(unit), "
        "raw_text=VALUES(raw_text), source_url=VALUES(source_url)",
        rows,
    )
    summary = {r[0]: r[2] for r in rows}
    print('  [学院简介] %d 项指标（在职教师 %s / 教授 %s / 博导 %s / 近五年论文 %s / 近五年经费 %s 万元）' % (
        len(rows), summary.get('teacher_total'), summary.get('teacher_professor'),
        summary.get('supervisor_phd'), summary.get('paper_total'), summary.get('fund_total')))
    return len(rows)


def run_once(max_pages, with_detail=False, detail_limit=0,
             with_teacher_profile=False, profile_limit=0, profile_retry=False):
    print('=== 官网真实数据采集 %s ===' % time.strftime('%Y-%m-%d %H:%M:%S'))
    conn = pymysql.connect(**DB)
    cur = conn.cursor()
    ensure_tables(cur)
    total = 0
    try:
        total += crawl_leaders(cur)
        total += crawl_teachers(cur)
        total += crawl_achievements(cur, max_pages)
        total += crawl_notices(cur, max_pages)
        crawl_profile_stats(cur)
        if with_teacher_profile:
            crawl_teacher_profiles(cur, profile_limit, retry_failed=profile_retry)
        if with_detail:
            crawl_notice_details(cur, detail_limit)
    finally:
        cur.close()
        conn.close()
    print('=== 完成，共 %d 条真实数据 ===' % total)
    return total


def run_schedule(hours, max_pages):
    from apscheduler.schedulers.blocking import BlockingScheduler

    def job():
        # 定时任务也把通知正文和教师详情带上，否则新发通知只有标题、新老师没有主页
        run_once(max_pages, with_detail=True, with_teacher_profile=True)

    sched = BlockingScheduler(timezone='Asia/Shanghai')
    sched.add_job(job, 'interval', hours=hours)
    print('定时采集已启动：每 %d 小时一次，Ctrl+C 退出' % hours)
    job()
    sched.start()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--once', action='store_true', help='采集一次后退出')
    ap.add_argument('--schedule', action='store_true', help='定时循环采集')
    ap.add_argument('--hours', type=int, default=6, help='定时周期（小时）')
    ap.add_argument('--pages', type=int, default=12, help='每个列表最多翻页数')
    ap.add_argument('--with-detail', action='store_true', help='同时补采通知公告正文（知识库全文检索用）')
    ap.add_argument('--detail-limit', type=int, default=0, help='本次最多补采几篇正文，0=全部')
    ap.add_argument('--teacher-profile', action='store_true', help='同时补采教师详情页（研究方向/简历）')
    ap.add_argument('--profile-limit', type=int, default=0, help='本次最多补采几位教师详情，0=全部')
    ap.add_argument('--profile-retry', action='store_true', help='重试之前失败的教师详情页（默认不重复抓）')
    args = ap.parse_args()

    if args.schedule:
        run_schedule(args.hours, args.pages)
    else:
        run_once(args.pages, with_detail=args.with_detail, detail_limit=args.detail_limit,
                 with_teacher_profile=args.teacher_profile, profile_limit=args.profile_limit,
                 profile_retry=args.profile_retry)


if __name__ == '__main__':
    main()
