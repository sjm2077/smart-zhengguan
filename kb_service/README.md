# 知识库与智能体服务（kb_service）

主门户「知识库问答」页面的后端。**独立进程、零额外依赖**（Python 标准库 + 仓库已有的 requests/bs4/pymysql），
不修改任何同学负责的业务子系统，只读官网爬取结果、真实 CSV 题录与制度文件。

## 1. 它能回答什么问题

| 类型 | 例子 | 背后工具 |
|---|---|---|
| 官方统计口径 | 学院有多少在职教师？近五年科研经费多少？ | `official_stats`（官网《学院简介》24 项） |
| 学术成果统计 | 学院官网学术成果每年有多少条？最新成果有哪些？ | `achievement_stats`（官网成果列表 597 条按年/类别计数 + 最近 6 条） |
| 教师信息 | 李爽是什么职称？费立国老师的研究方向是什么？ | `faculty_lookup` + `kb_search(faculty)`（名录 93 人，详情 88 人） |
| 通知公告 | 最新通知有哪些？博士后招聘条件？ | `notice_search`（899 条，含 619 篇正文） |
| 制度条款 | 研究生奖学金评审办法有哪些规定？学籍管理规定？ | `kb_search`（制度文件 7 份） |
| 论文成果 | 谁研究地方政府信任？ | `kb_search`（官网论文题录 395 + CNKI 题录） |
| 平台自述 | 我们平台的大屏是怎么做的？ | `kb_search`（项目汇报文档，仅问平台类问题时参与） |
| 无关问题（负向） | 火星殖民的氧气循环方案？ | 直接回答"知识库没有检索到"，**不编造** |

## 2. 数据来源与可信级别

| 级别 | 内容 | 来源 |
|---|---|---|
| A 官网真实 | 教师 93（详情 88）/ 学术成果 597 / 通知 899（正文 619）/ 学院简介 24 项 | 爬虫 `scripts/crawler_pspa.py` → MySQL `zhhengguan_research` |
| B 真实采集文件 | 官网论文题录 395、CNKI 题录、教师履历 | `data/*.csv`、`data/teachers.json`（GBK/UTF-8 已适配） |
| C 制度文件 | 研究生文件规定 7 份 | `smartzhengguan/.../研究生文件规定/*.txt` |
| D 平台文档 | 项目汇报、规划书 | 仓库根目录 md |

当前规模：**文档 2032 篇 / 分块 5453 / 词表 88285**（2026-10-26 构建，1.3s）。
学术成果与通知公告都是官网栏目全量翻页（45 页）抓的，时间跨度分别为 2019-05~2026-10、2019-03~2026-09。

教师详情一项的口径说明（答辩时可能会被问）：93 位教师里 88 位采到了个人主页正文，
其余 4 位官网页面本身就是空的、1 位主页需登录 —— 这 5 人已在 `api_pspa_teacher.profile_status`
里记下失败原因，爬虫不会反复重抓，知识库里也如实标注"暂未采集到个人详情页"。

## 3. 目录结构

```
kb_service/
├── config.py      配置：路径、MySQL、切块/检索参数、LLM 三模式
├── search.py      中文二元分词 + BM25 倒排索引 + 同义词扩展 + 覆盖度加权（pickle 持久化）
├── ingest.py      建库：四类数据源 → 切块 → 建索引 → meta.json
├── agent.py       智能体：意图规划 → 调工具 → 拼引用 → 生成/降级
├── server.py      HTTP 服务（标准库 ThreadingHTTPServer）
├── selftest.py    13 条问答回归用例（含负向拒答）
└── data/          kb.pkl（索引）、meta.json（元数据、成果统计、教师名录）
```

## 4. 用法

```powershell
# 1) 建库 / 重建（官网爬虫跑完后执行）
& "c:\zhenguan\research_system\venv\Scripts\python.exe" kb_service\ingest.py

# 2) 启动服务（默认 127.0.0.1:8900，前端经 Vite 代理 /kb 访问）
& "c:\zhenguan\research_system\venv\Scripts\python.exe" kb_service\server.py

# 3) 回归自测（默认强制纯检索，结果可复现；加 --llm 测生成模式）
& "c:\zhenguan\research_system\venv\Scripts\python.exe" kb_service\selftest.py -v

# 4) 官网数据 → 重建索引 一条命令
& "c:\zhenguan\scripts\refresh_kb.ps1"
```

## 5. 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 索引状态、分块数、大模型模式 |
| GET | `/stats` | 知识库构成（按类型）、官方口径数字、数据覆盖（`corpus`/`achievement`）、来源清单 |
| GET | `/search?q=&topk=&type=` | 检索，`type` 可选 `notice/policy/achievement/faculty/paper/profile` |
| POST | `/ask` `{"question": "..."}` | 智能体问答，返回 `answer / citations / tools_used / mode` |
| GET | `/faculty?name=&dept=&title=` | 官网教师名录过滤（含研究方向） |
| GET | `/notices?q=&limit=` | 官网通知公告 |
| POST | `/rebuild` | 重建索引（爬虫更新后调用） |

## 6. 大模型配置（可选）

三种模式，优先级从上到下：

1. `kb_service/.env` 里配 `KB_LLM_API_KEY` + `KB_LLM_BASE_URL`（OpenAI 兼容接口）→ 直连生成；
2. **默认**：`KB_LLM_PROXY=http://127.0.0.1:8000/api/v1/chat-proxy/` → 复用研究生系统已有的后端代理，
   Key 只在那个服务的 `.env` 里，不落到本服务、更不落到前端（主门户 AI 助手走的也是这条路）；
3. 两者都不可用 → **纯检索模式**：只返回原文摘录 + 引用，界面明确标注"未配置大模型 Key"。

> Key 只允许放 `kb_service/.env` 或系统环境变量，**不要写进前端**。

## 7. 检索是怎么做的（为什么不用向量库）

1. **中文二元分词**：不依赖 jieba（避免引入新依赖），按二字滑窗切词，ASCII 词单独切；
2. **BM25 打分**：标题词二次计入，长文档做长度归一（k1=1.5, b=0.75）；
3. **同义词扩展**：`师资↔教师/教授`、`经费↔科研经费`、`研究方向↔研究领域` 等 15 组，扩展词权重 0.45；
4. **覆盖度门槛**：命中不同查询词的比例 < 0.25 的块直接丢弃（实测外行问题 0.14~0.21，正常问题 ≥0.30），
   宁可回答"未检索到"，也不用不相干内容凑数；
5. **按标题+来源去重**：同一篇文档被切成多块时只保留最高分那块。

## 8. 已知短板（答辩时如实说明）

1. **没有向量检索**：BM25 是字面匹配，语义相近但用词完全不同的问法（"钱不够花了" vs "经费执行率低"）召不准；
2. **切块未按条款层级**：固定 450 字重叠切块，条款级精确定位能力弱；
3. **增量更新为全量重建**：`ingest.py` 每次重建整个索引（1.3s，可接受但不够优雅）；
4. **单 Agent**：只有 1 个 Agent + 5 个只读工具，没有 Text-to-SQL、图表生成、业务流转、多 Agent 协同；
5. **教师详情有缺口**：88/93 人，5 人官网页面空或需登录，不是抓取逻辑漏了（`--profile-retry` 可定期重试）。

升级路径（需预算/决策）：BGE 或 m3e Embedding → 向量库（Qdrant/pgvector）→ 混合检索 + Rerank → 条款级切块。

