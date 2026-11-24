/* Research department presentation fallback v1.
 * Real API values take precedence. Demo values are used only when a field is empty,
 * missing, or contains no positive chart values. Clearly labelled in the UI footer.
 */
(function () {
  const years = ['2021', '2022', '2023', '2024', '2025'];
  const demos = {
    political: {
      stat_cards: {teacher_count: 36, project_count: 48, total_fund: '1,286.5', achievement_count: 216, high_level_ratio: 42.6, csci_growth: 12.8},
      fund_trend: {all:[186,218,245,291,346], national:[82,96,112,135,158], provincial:[46,55,61,72,86], school:[28,31,36,39,45], horizontal:[30,36,36,45,57]},
      ring_data: [{name:'期刊论文',value:86},{name:'研究报告',value:48},{name:'学术专著',value:32},{name:'会议论文',value:28},{name:'其他成果',value:22}],
      bar_categories:['核心期刊','CSSCI/扩展版','一般期刊','学术专著','研究报告'],
      bar_values:[38,52,61,32,48],
      radar_labels:['政治思想与理论','比较政治与制度','政党政治','民主与治理','公共政策与智库'],
      radar_data:[82,76,68,88,79],
      wordcloud_data:[['国家治理',96],['政治制度',88],['公共政策',82],['基层治理',76],['民主发展',70],['政党研究',64],['社会政策',59],['比较政治',54],['数字政府',48],['公共服务',43]].map(x=>({name:x[0],value:x[1]})),
      achievements_table:[
        {序号:1,成果名称:'数字时代国家治理能力现代化研究',负责人:'张明',成果类型:'CSSCI论文',年度:2025},
        {序号:2,成果名称:'基层治理体系与治理效能提升路径',负责人:'李华',成果类型:'学术专著',年度:2025},
        {序号:3,成果名称:'全过程人民民主的制度优势与实践机制',负责人:'王宁',成果类型:'CSSCI论文',年度:2024},
        {序号:4,成果名称:'地方政府公共政策执行力评估研究',负责人:'陈静',成果类型:'研究报告',年度:2024},
        {序号:5,成果名称:'比较政治视野下的政党制度发展',负责人:'刘洋',成果类型:'核心期刊',年度:2023},
        {序号:6,成果名称:'公共服务均等化与区域协调发展',负责人:'赵敏',成果类型:'CSSCI论文',年度:2023}
      ],
      projects_table:[
        {项目名称:'国家治理现代化重大理论与实践问题研究',负责人:'张明',项目类型:'国家社科基金重点项目',进度:'85%',状态:'在研'},
        {项目名称:'基层治理数字化转型机制研究',负责人:'李华',项目类型:'国家社科基金一般项目',进度:'70%',状态:'在研'},
        {项目名称:'全过程人民民主基层实践研究',负责人:'王宁',项目类型:'教育部人文社科项目',进度:'100%',状态:'已结项'},
        {项目名称:'地方政府政策执行效能评价',负责人:'陈静',项目类型:'省社科规划项目',进度:'60%',状态:'在研'},
        {项目名称:'比较政治与制度变迁研究',负责人:'刘洋',项目类型:'校级科研项目',进度:'45%',状态:'在研'}
      ]
    },
    international: {
      stat_cards:{country_coverage:28,international_projects:19,total_foreign_fund:'426.8',international_publications:73,national_foreign_ratio:31.5,academic_exchange_growth:16.2},
      fund_trend:{years,domestic:[88,102,116,128,145],foreign:[18,22,25,31,38]},
      continents:['东亚与东南亚','欧洲','北美','中东与非洲','拉美地区','中亚地区'],
      continent_data:[32,25,19,14,11,8],
      ring_data:[{name:'区域国别研究',value:31},{name:'国际关系理论',value:24},{name:'国际安全',value:19},{name:'全球治理',value:15},{name:'外交与战略',value:11}],
      radar_labels:['地缘政治与区域格局','大国关系与战略竞争','全球治理与国际组织','区域国别研究','国际安全'],
      radar_data:[78,86,73,91,82],
      wordcloud_data:[['大国关系',98],['区域国别',91],['全球治理',84],['国际安全',78],['地缘政治',72],['国际组织',66],['外交战略',60],['亚太秩序',55],['一带一路',49],['国际发展',43]].map(x=>({name:x[0],value:x[1]})),
      achievements_table:[
        {序号:1,成果名称:'全球治理体系变革与中国参与研究',负责人:'周明',成果类型:'SSCI论文',发布年份:2025},
        {序号:2,成果名称:'东亚区域合作与国际秩序演变',负责人:'林涛',成果类型:'学术专著',发布年份:2025},
        {序号:3,成果名称:'大国战略竞争背景下的国际安全',负责人:'吴倩',成果类型:'CSSCI论文',发布年份:2024},
        {序号:4,成果名称:'中东地区政治转型与国家治理',负责人:'郑宇',成果类型:'研究报告',发布年份:2024},
        {序号:5,成果名称:'国际组织与全球公共产品供给',负责人:'孙悦',成果类型:'核心期刊',发布年份:2023},
        {序号:6,成果名称:'区域国别研究方法与案例分析',负责人:'何峰',成果类型:'学术专著',发布年份:2023}
      ],
      projects_table:[
        {项目名称:'全球治理与国际秩序变革研究',负责人:'周明',项目类型:'国家社科基金重点项目',进度:'82%',状态:'在研'},
        {项目名称:'东亚区域合作机制比较研究',负责人:'林涛',项目类型:'教育部人文社科项目',进度:'68%',状态:'在研'},
        {项目名称:'国际安全形势与风险评估',负责人:'吴倩',项目类型:'省社科规划项目',进度:'100%',状态:'已结项'},
        {项目名称:'中东国家政治发展跟踪研究',负责人:'郑宇',项目类型:'校级科研项目',进度:'55%',状态:'在研'},
        {项目名称:'国际组织治理效能研究',负责人:'孙悦',项目类型:'横向合作项目',进度:'40%',状态:'在研'}
      ]
    },
    public: {
      stat_cards:{gov_projects:32,total_fund:'968.2',core_achievements:148,digital_gov_projects:18,community_growth:14.6,emergency_projects:12},
      fund_trend:{years,vertical:[126,148,172,196,225],horizontal:[38,45,51,63,78]},
      directions:['数字政府与数字治理','基层与社区治理','应急管理与风险治理','公共政策与绩效评估','政府改革与公共服务','社会保障与社会组织'],
      dir_counts:[42,38,29,24,19,16],
      pie_data:[{name:'国家级项目',value:28},{name:'省部级项目',value:34},{name:'市厅级项目',value:22},{name:'横向合作项目',value:16}],
      radar_values:[91,88,76,72,68,81],
      wordcloud_data:[['数字治理',98],['社区治理',91],['应急管理',84],['基层政府',78],['公共服务',72],['政策评估',66],['社会组织',60],['智慧城市',55],['风险治理',49],['政府改革',43]].map(x=>({name:x[0],value:x[1]})),
      result_years:years,
      journal_counts:[18,22,26,31,36],
      monograph_counts:[5,6,7,8,10],
      report_counts:[9,12,14,18,21],
      achievements_table:[
        {序号:1,成果名称:'数字政府建设与公共服务效能提升研究',负责人:'王芳',成果类型:'CSSCI论文',发布年份:2025},
        {序号:2,成果名称:'城市社区治理共同体建设路径研究',负责人:'刘伟',成果类型:'学术专著',发布年份:2025},
        {序号:3,成果名称:'基层应急管理体系现代化研究',负责人:'陈立',成果类型:'研究报告',发布年份:2024},
        {序号:4,成果名称:'公共政策绩效评估的指标体系与应用',负责人:'赵静',成果类型:'CSSCI论文',发布年份:2024},
        {序号:5,成果名称:'社会组织参与基层治理的机制研究',负责人:'孙敏',成果类型:'核心期刊',发布年份:2023},
        {序号:6,成果名称:'地方政府数字化转型案例研究',负责人:'周凯',成果类型:'研究报告',发布年份:2023}
      ],
      projects_table:[
        {项目名称:'数字政府背景下公共服务流程再造研究',负责人:'王芳',项目类型:'国家社科基金一般项目',进度:'78%',状态:'在研'},
        {项目名称:'城市社区治理共同体建设研究',负责人:'刘伟',项目类型:'省社科规划项目',进度:'65%',状态:'在研'},
        {项目名称:'基层应急管理能力评价与提升研究',负责人:'陈立',项目类型:'教育部人文社科项目',进度:'100%',状态:'已结项'},
        {项目名称:'公共政策绩效第三方评估机制研究',负责人:'赵静',项目类型:'市厅级项目',进度:'52%',状态:'在研'},
        {项目名称:'社会组织参与社区治理实践研究',负责人:'孙敏',项目类型:'横向合作项目',进度:'40%',状态:'在研'}
      ],
      analysis:{summary:'本年度公共管理学科在数字治理、社区治理方向形成较为集中的成果积累，科研项目与学术成果保持稳步增长。',weak:'政府改革与公共服务方向的成果数量相对偏少，跨方向协同研究仍有提升空间。',suggest:'建议围绕数字治理与社区治理优势方向开展交叉研究，同时加强应急管理、政策评估等方向的项目培育。'}
    },
    science: {
      stat_cards:{teacher_count:24,project_count:31,total_fund:'586.4',achievement_count:126,national_ratio:38.5,young_output_rate:11.6},
      pie_data:[{name:'学术论文',value:52},{name:'学术专著',value:24},{name:'研究报告',value:28},{name:'其他成果',value:22}],
      bar_categories:['国家级项目','省部级项目','市厅级项目','校级项目','横向项目'],
      bar_values:[8,13,6,11,5],
      wordcloud_data:[['科学社会主义',98],['马克思主义中国化',91],['社会主义发展',84],['理论创新',78],['共同富裕',72],['中国式现代化',66],['意识形态',60],['社会发展',55],['政治经济学',49],['历史经验',43]].map(x=>({name:x[0],value:x[1]})),
      trend_years:years,
      trend_series:[{name:'学术论文',data:[14,17,20,24,29]},{name:'学术专著',data:[4,5,6,7,8]},{name:'研究报告',data:[6,8,9,12,14]}],
      bubble_data:[
        {teacher_id:null,name:'教师A',value:[86,88,82]},
        {teacher_id:null,name:'教师B',value:[78,83,76]},
        {teacher_id:null,name:'教师C',value:[91,79,85]},
        {teacher_id:null,name:'教师D',value:[73,76,70]},
        {teacher_id:null,name:'教师E',value:[82,91,84]},
        {teacher_id:null,name:'教师F',value:[88,85,87]}
      ],
      achievements_table:[
        {序号:1,成果名称:'科学社会主义理论创新与时代发展研究',负责人:'高峰',类型:'CSSCI论文',年份:2025},
        {序号:2,成果名称:'中国式现代化的理论逻辑与实践路径',负责人:'马宁',类型:'学术专著',年份:2025},
        {序号:3,成果名称:'马克思主义中国化时代化研究',负责人:'刘晨',类型:'CSSCI论文',年份:2024},
        {序号:4,成果名称:'共同富裕的制度基础与实现机制',负责人:'周敏',类型:'研究报告',年份:2024},
        {序号:5,成果名称:'世界社会主义发展比较研究',负责人:'陈宇',类型:'核心期刊',年份:2023},
        {序号:6,成果名称:'新时代意识形态建设研究',负责人:'赵琳',类型:'学术专著',年份:2023}
      ],
      projects_table:[
        {项目名称:'新时代科学社会主义重大理论问题研究',负责人:'高峰',级别:'国家级',进度:'86%',状态:'在研'},
        {项目名称:'中国式现代化理论体系研究',负责人:'马宁',级别:'省部级',进度:'72%',状态:'在研'},
        {项目名称:'马克思主义中国化时代化研究',负责人:'刘晨',级别:'国家级',进度:'100%',状态:'已结项'},
        {项目名称:'共同富裕与社会发展研究',负责人:'周敏',级别:'省部级',进度:'58%',状态:'在研'},
        {项目名称:'世界社会主义发展趋势研究',负责人:'陈宇',级别:'校级',进度:'45%',状态:'在研'}
      ]
    }
  };

  function positive(arr) {
    return Array.isArray(arr) && arr.some(v => {
      if (v && typeof v === 'object') {
        if (Array.isArray(v.data)) return v.data.some(n => Number(n) > 0);
        if (Array.isArray(v.value)) return v.value.some(n => Number(n) > 0);
        return Number(v.value) > 0;
      }
      return Number(v) > 0;
    });
  }
  function fill(obj, key, fallback, needsPositive) {
    if (!Array.isArray(obj[key]) || obj[key].length === 0 || (needsPositive && !positive(obj[key]))) {
      obj[key] = fallback.map(v => v && typeof v === 'object' ? {...v} : v);
    }
  }
  function apply(dept, payload) {
    const demo = demos[dept];
    const data = payload && typeof payload === 'object' ? payload : {};
    if (!demo) return data;
    data.stat_cards = data.stat_cards && typeof data.stat_cards === 'object' ? data.stat_cards : {};
    Object.keys(demo.stat_cards || {}).forEach(k => {
      if (data.stat_cards[k] === undefined || data.stat_cards[k] === null || data.stat_cards[k] === '') data.stat_cards[k] = demo.stat_cards[k];
    });
    Object.keys(demo).forEach(k => {
      if (k === 'stat_cards' || k === 'analysis' || k === 'fund_trend') return;
      fill(data, k, demo[k], ['ring_data','pie_data','radar_data','radar_values','bar_values','dir_counts','continent_data','journal_counts','monograph_counts','report_counts','trend_series','bubble_data'].includes(k));
    });
    if (demo.fund_trend) {
      data.fund_trend = data.fund_trend && typeof data.fund_trend === 'object' ? data.fund_trend : {};
      Object.keys(demo.fund_trend).forEach(k => {
        if (k === 'years') {
          if (!Array.isArray(data.fund_trend[k]) || !data.fund_trend[k].length) data.fund_trend[k] = demo.fund_trend[k].slice();
        } else if (!Array.isArray(data.fund_trend[k]) || !positive(data.fund_trend[k])) {
          data.fund_trend[k] = demo.fund_trend[k].slice();
        }
      });
    }
    if (demo.analysis) {
      data.analysis = data.analysis && typeof data.analysis === 'object' ? data.analysis : {};
      Object.keys(demo.analysis).forEach(k => {
        if (!data.analysis[k]) data.analysis[k] = demo.analysis[k];
      });
    }
    data.__demo_fallback_used = true;
    return data;
  }

  const routeMap = [
    ['/api/dept/political', 'political'],
    ['/api/dept/international', 'international'],
    ['/api/dept/public', 'public'],
    ['/api/dept/science', 'science']
  ];
  const originalFetch = window.fetch.bind(window);
  window.fetch = function(input, init) {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const match = routeMap.find(([path]) => url.indexOf(path) >= 0);
    if (!match) return originalFetch(input, init);
    const dept = match[1];
    return originalFetch(input, init).then(async response => {
      if (!response.ok) return new Response(JSON.stringify(apply(dept, {})), {status:200, headers:{'Content-Type':'application/json'}});
      try {
        const payload = await response.clone().json();
        return new Response(JSON.stringify(apply(dept, payload)), {status:200, headers:{'Content-Type':'application/json'}});
      } catch (e) {
        return new Response(JSON.stringify(apply(dept, {})), {status:200, headers:{'Content-Type':'application/json'}});
      }
    }).catch(() => new Response(JSON.stringify(apply(dept, {})), {status:200, headers:{'Content-Type':'application/json'}}));
  };
  window.ResearchDeptDemo = {apply};
})();
