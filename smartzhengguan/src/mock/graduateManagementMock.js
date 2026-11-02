import { REAL_GRADES, REAL_MAJORS } from '../utils/graduateCatalog'

export const sharedOptions = {
  grades: [...REAL_GRADES],
  majors: [...REAL_MAJORS],
  degreeTypes: ['学术型硕士', '专业型硕士', '博士'],
  enrollmentTypes: ['硕士', '博士', '国际学生'],
  studentStatuses: ['正常在籍', '休学', '退学', '延期毕业', '其他'],
  trainingStages: ['课程学习', '论文开题', '中期考核', '论文答辩'],
  trainingStatuses: ['待提交', '待审核', '审核通过', '驳回修改'],
}

export const homeMockData = {
  updatedAt: '2026-05-13 08:30:00',
  headline: {
    title: '学院研究生数据概览',
    subtitle: '聚焦政治学与公共管理学院研究生核心指标',
    totalStudents: 3256,
    masterCount: 2654,
    doctorCount: 602,
    internationalCount: 170,
    annualGraduates: 856,
  },
  primaryAction: { label: '刷新预测', message: '预测分析结果已刷新' },
  statCards: [
    { title: '学院在读研究生总数', number: 3256, icon: '总', changeLabel: '较上年 ↑8.3%' },
    { title: '学院硕士研究生', number: 2654, icon: '硕', changeLabel: '较上年 ↑7.1%' },
    { title: '学院博士研究生', number: 602, icon: '博', changeLabel: '较上年 ↑12.6%' },
    { title: '学院国际学生', number: 170, icon: '际', changeLabel: '较上年 ↑15.3%' },
    { title: '学院本年毕业研究生', number: 856, icon: '毕', changeLabel: '较上年 ↑9.4%' },
    { title: '学院境内学生', number: 3086, icon: '内', changeLabel: '较上年 ↑7.8%' },
  ],
  charts: {
    trend: [
      { year: '2019', master: 2006, doctor: 310 },
      { year: '2020', master: 2102, doctor: 350 },
      { year: '2021', master: 2200, doctor: 400 },
      { year: '2022', master: 2450, doctor: 480 },
      { year: '2023', master: 2600, doctor: 550 },
      { year: '2024', master: 2654, doctor: 602 },
    ],
    gender: [
      { name: '男生', value: 2020 },
      { name: '女生', value: 1236 },
    ],
    grades: [
      { name: '一年级', value: 1025 },
      { name: '二年级', value: 912 },
      { name: '三年级', value: 656 },
      { name: '四年级', value: 364 },
      { name: '五年级+', value: 109 },
    ],
    sourceRegions: [
      { name: '山东', value: 682 },
      { name: '江苏', value: 356 },
      { name: '河南', value: 298 },
      { name: '广东', value: 220 },
      { name: '湖北', value: 195 },
      { name: '上海', value: 168 },
      { name: '浙江', value: 168 },
      { name: '北京', value: 145 },
      { name: '湖南', value: 132 },
      { name: '河北', value: 121 },
      { name: '甘肃', value: 121 },
      { name: '辽宁', value: 110 },
    ],
  },
  notices: [
    { title: '山东大学2026年研究生学术之星·优秀成果奖公示', date: '05-25', url: 'https://www.grad.sdu.edu.cn/content3.jsp?urltype=news.NewsContentUrl&wbtreeid=1164&wbnewsid=20951' },
    { title: '关于申报2026年山东大学"AI+"研究生暑期学校的通知', date: '05-22', url: 'https://www.grad.sdu.edu.cn/content3.jsp?urltype=news.NewsContentUrl&wbtreeid=1041&wbnewsid=20943' },
    { title: '关于选派2025级硕士研究生赴厦门大学访学的通知', date: '05-20', url: 'https://www.grad.sdu.edu.cn/content3.jsp?urltype=news.NewsContentUrl&wbtreeid=1037&wbnewsid=20942' },
    { title: '关于开展2026年研究生学籍信息核对工作的通知', date: '05-13', url: 'https://www.grad.sdu.edu.cn/' },
    { title: '关于2026届研究生学位申请阶段工作的通知', date: '05-10', url: 'https://www.grad.sdu.edu.cn/' },
  ],
  todos: [
    { label: '培养计划审核', count: 23 },
    { label: '学籍变更审核', count: 15 },
    { label: '奖助学金审核', count: 8 },
    { label: '答辩安排确认', count: 6 },
    { label: '开题报告审核', count: 12 },
    { label: '导师分配确认', count: 9 },
    { label: '课程成绩录入', count: 5 },
  ],
}

export const admissionMockData = {
  updatedAt: '2026-05-12',
  filters: {
    default: {
      year: '2024',
      type: '硕士',
      direction: '全部',
      source: '全部',
    },
    years: ['2020', '2021', '2022', '2023', '2024'],
    types: ['全部', '硕士', '博士', '国际学生'],
    directions: ['全部', ...sharedOptions.majors],
    sources: ['全部', '985高校', '211高校', '双一流高校', '普通高校', '本校直升'],
  },
  statCards: [
    { title: '报名人数', number: 4782, changeLabel: '较去年 ↑12.5%' },
    { title: '初审通过人数', number: 3125, changeLabel: '较去年 ↑8.3%' },
    { title: '复试人数', number: 1256, changeLabel: '较去年 ↑5.7%' },
    { title: '拟录取人数', number: 856, changeLabel: '较去年 ↑6.2%' },
    { title: '录取率', number: '92.3%', changeLabel: '较去年 ↑3.1%' },
  ],
  charts: {
    applyTrend: [
      { year: '2020', value: 2845 },
      { year: '2021', value: 3201 },
      { year: '2022', value: 3650 },
      { year: '2023', value: 4248 },
      { year: '2024', value: 4782 },
    ],
    majorTop: [
      { name: '政治学理论', value: 698 },
      { name: '科学社会主义与国际共产主义运动', value: 566 },
      { name: '国际政治', value: 312 },
      { name: '统一战线学', value: 56 },
      { name: '中共党史', value: 51 },
      { name: '行政管理', value: 15 },
      { name: '国际关系', value: 13 },
      { name: '应急管理', value: 3 },
    ],
    sourceDistribution: [
      { name: '山东省', value: 32.6 },
      { name: '河南省', value: 12.8 },
      { name: '河北省', value: 9.7 },
      { name: '江苏省', value: 7.6 },
      { name: '其他', value: 37.3 },
    ],
  },
  progress: [
    { stage: '网上报名', startTime: '2023-09-01', endTime: '2023-10-31', status: '已结束', completionPercent: 100 },
    { stage: '资格初审', startTime: '2023-11-01', endTime: '2023-11-20', status: '已结束', completionPercent: 100 },
    { stage: '复试', startTime: '2024-03-15', endTime: '2024-03-30', status: '已结束', completionPercent: 100 },
    { stage: '拟录取', startTime: '2024-04-01', endTime: '2024-04-15', status: '进行中', completionPercent: 75 },
    { stage: '录取通知', startTime: '2024-06-01', endTime: '2024-06-30', status: '未开始', completionPercent: 0 },
  ],
  notices: [
    { title: '关于公布 2024 年研究生拟录取名单的通知', date: '2024-05-10' },
    { title: '山东大学 2024 年研究生复试工作安排', date: '2024-03-05' },
    { title: '2024 年研究生招生考试初试成绩查询通知', date: '2024-02-26' },
    { title: '关于 2024 年研究生招生专业目录的说明', date: '2023-09-20' },
    { title: '山东大学 2024 年研究生招生简章', date: '2023-09-01' },
  ],
}

export const academicStatusMockData = {
  statCards: [
    { title: '学院在籍学生', number: 3258, changeLabel: '在籍规模稳定' },
    { title: '学院注册人数', number: 3210, changeLabel: '注册率 98.5%' },
    { title: '学院异动人数', number: 28, changeLabel: '异动率 0.86%' },
    { title: '学院退学/休学', number: 20, changeLabel: '退学率 0.61%' },
    { title: '学院异动上报', number: 15682, changeLabel: '本年累计' },
  ],
  charts: {
    gradeDistribution: [
      { grade: '2025级', male: 3.5, female: 5.5 },
      { grade: '2024级', male: 10.2, female: 13.9 },
      { grade: '2023级', male: 16.8, female: 11.6 },
      { grade: '2022级', male: 28.1, female: 10.4 },
    ],
    majorTop: [
      { name: '政治学类', value: 312 },
      { name: '公共管理类', value: 248 },
      { name: '政治学理论', value: 210 },
      { name: '科学社会主义与国际共产主义运动', value: 185 },
      { name: '中共党史', value: 168 },
      { name: '国际政治', value: 152 },
      { name: '国际关系', value: 135 },
      { name: '统一战线学', value: 118 },
      { name: '行政管理', value: 102 },
      { name: '应急管理', value: 85 },
    ],
    statusDistribution: [
      { name: '正常在籍', value: 84.2 },
      { name: '休学', value: 3.5 },
      { name: '退学', value: 1.8 },
      { name: '其他', value: 10.5 },
    ],
    changeTrend: [
      { year: '2020', count: 18, growth: 0 },
      { year: '2021', count: 22, growth: 22.2 },
      { year: '2022', count: 31, growth: 40.9 },
      { year: '2023', count: 25, growth: -19.4 },
      { year: '2024', count: 28, growth: 12.0 },
    ],
  },
  records: [
    { id: '2024050001', name: '张三', changeType: '休学', handler: '林老师', reason: '个人原因', date: '2024-05-10', status: '办理中', tagType: 'warning' },
    { id: '2024050002', name: '李四', changeType: '复学', handler: '孙老师', reason: '学业回归', date: '2024-05-09', status: '已通过', tagType: 'success' },
    { id: '2024050003', name: '王五', changeType: '退学', handler: '赵老师', reason: '就业原因', date: '2024-05-08', status: '已通过', tagType: 'danger' },
    { id: '2024050004', name: '赵六', changeType: '变更专业', handler: '钱老师', reason: '跨专业申请', date: '2024-05-07', status: '办理中', tagType: 'warning' },
    { id: '2024050005', name: '孙七', changeType: '休学', handler: '周老师', reason: '健康原因', date: '2024-05-06', status: '已通过', tagType: 'success' },
  ],
}

export const trainingMockData = {
  filters: {
    default: { grade: '', major: '', stage: '', status: '' },
    grades: sharedOptions.grades,
    majors: sharedOptions.majors,
    stages: sharedOptions.trainingStages,
    statuses: sharedOptions.trainingStatuses,
  },
  statCards: [
    { title: '培养计划总数', number: '12项', changeLabel: '当前筛选结果' },
    { title: '待审核计划', number: '4项', changeLabel: '需本周完成处理' },
    { title: '平均完成率', number: '56%', changeLabel: '已通过 5 项' },
    { title: '导师确认率', number: '83%', changeLabel: '按当前记录统计' },
  ],
  charts: {
    planCompletion: [
      { name: '已完成', value: 58 },
      { name: '进行中', value: 22 },
      { name: '未开始', value: 15 },
      { name: '已终止', value: 5 },
    ],
    completionTrend: [
      { year: '2020', actual: 76.8, target: 85 },
      { year: '2021', actual: 79.2, target: 85 },
      { year: '2022', actual: 82.1, target: 85 },
      { year: '2023', actual: 84.6, target: 85 },
      { year: '2024', actual: 87.3, target: 85 },
    ],
    statusDistribution: [
      { name: '待提交', value: 2 },
      { name: '待审核', value: 4 },
      { name: '审核通过', value: 5 },
      { name: '驳回修改', value: 2 },
    ],
    gradeCompletion: [
      { grade: '2022级', value: 92 },
      { grade: '2023级', value: 68 },
      { grade: '2024级', value: 51 },
      { grade: '2025级', value: 21 },
    ],
    stageDistribution: [
      { name: '课程学习', value: 5 },
      { name: '论文开题', value: 2 },
      { name: '中期考核', value: 2 },
      { name: '论文答辩', value: 3 },
    ],
    evaluationDistribution: [
      { name: '优秀', value: 35 },
      { name: '良好', value: 40 },
      { name: '合格', value: 18 },
      { name: '不合格', value: 7 },
    ],
    radar: [
      { name: '课程质量', value: 4.2 },
      { name: '就业指导', value: 3.8 },
      { name: '学术支持', value: 4.5 },
      { name: '实践教学', value: 3.6 },
      { name: '导师指导', value: 4.0 },
    ],
  },
  plans: [
    { studentId: '20240001', name: '张晨', grade: '2024级', major: '行政管理', degreeType: '学术型硕士', stage: '课程学习', advisor: '刘老师', status: '待审核', tagType: 'warning', updatedAt: '2026-05-10', completion: 45 },
    { studentId: '20240008', name: '李玥', grade: '2024级', major: '政治学理论', degreeType: '学术型硕士', stage: '课程学习', advisor: '周老师', status: '审核通过', tagType: 'success', updatedAt: '2026-05-08', completion: 62 },
    { studentId: '20230016', name: '王哲', grade: '2023级', major: '科学社会主义与国际共产主义运动', degreeType: '博士', stage: '论文开题', advisor: '陈老师', status: '待审核', tagType: 'warning', updatedAt: '2026-05-09', completion: 58 },
    { studentId: '20230027', name: '赵宁', grade: '2023级', major: '国际关系', degreeType: '学术型硕士', stage: '中期考核', advisor: '黄老师', status: '审核通过', tagType: 'success', updatedAt: '2026-05-07', completion: 76 },
    { studentId: '20230041', name: '孙睿', grade: '2023级', major: '统一战线学', degreeType: '专业型硕士', stage: '课程学习', advisor: '许老师', status: '驳回修改', tagType: 'danger', updatedAt: '2026-05-06', completion: 39 },
    { studentId: '20220005', name: '吴楠', grade: '2022级', major: '国际政治', degreeType: '博士', stage: '论文答辩', advisor: '马老师', status: '审核通过', tagType: 'success', updatedAt: '2026-05-05', completion: 96 },
    { studentId: '20220011', name: '郑航', grade: '2022级', major: '中共党史', degreeType: '学术型硕士', stage: '论文答辩', advisor: '谢老师', status: '待提交', tagType: 'info', updatedAt: '2026-05-03', completion: 88 },
    { studentId: '20250003', name: '何清', grade: '2025级', major: '应急管理', degreeType: '专业型硕士', stage: '课程学习', advisor: '朱老师', status: '待提交', tagType: 'info', updatedAt: '2026-05-11', completion: 18 },
  ],
  notices: [
    { title: '2026年春季学期培养计划调整截止时间通知', date: '05-12', read: false },
    { title: '博士研究生开题备案材料提交提醒', date: '05-10', read: false },
    { title: '中期考核结果录入工作安排', date: '05-08', read: true },
    { title: '课程成绩同步异常名单待处理', date: '05-06', read: false },
    { title: '毕业资格预审材料提交通知', date: '04-28', read: true },
  ],
  todos: [
    { label: '待审核培养计划', count: 18 },
    { label: '待导师确认', count: 9 },
    { label: '待补交材料', count: 6 },
    { label: '本周到期任务', count: 4 },
  ],
}

export const degreeMockData = {
  updatedAt: '2024-05-20 10:30:00',
  statCards: [
    { title: '学院学位申请总数', number: 128, changeLabel: '较上期 ↑4.6%' },
    { title: '学院待审核学位申请', number: 36, changeLabel: '本月新增 8人' },
    { title: '学院论文提交总数', number: 92, changeLabel: '较上期 ↑6.2%' },
    { title: '学院学位授予总数', number: 866, changeLabel: '本年已授予 152人' },
  ],
  charts: {
    applicationTypes: [
      { name: '学术学位', value: 664 },
      { name: '专业学位', value: 615 },
    ],
    applicationTrend: [
      { year: '2020', count: 98, growth: 0 },
      { year: '2021', count: 112, growth: 14.3 },
      { year: '2022', count: 115, growth: 2.7 },
      { year: '2023', count: 121, growth: 5.2 },
      { year: '2024', count: 128, growth: 5.8 },
    ],
    paperReview: [
      { name: '通过', value: 71.0 },
      { name: '修改后通过', value: 22.0 },
      { name: '不通过', value: 7.0 },
    ],
    defenseResults: [
      { name: '答辩通过', value: 778, percent: 84.6 },
      { name: '修改后通过', value: 120, percent: 13.1 },
      { name: '不通过', value: 21, percent: 2.3 },
    ],
    awardTrend: [
      { year: '2020', value: 745 },
      { year: '2021', value: 782 },
      { year: '2022', value: 821 },
      { year: '2023', value: 856 },
      { year: '2024', value: 866 },
    ],
    disciplineDistribution: [
      { name: '政治学理论', count: 218, cumulative: 20.5 },
      { name: '科学社会主义与国际共产主义运动', count: 195, cumulative: 38.7 },
      { name: '中共党史', count: 156, cumulative: 53.3 },
      { name: '国际政治', count: 177, cumulative: 69.9 },
      { name: '国际关系', count: 168, cumulative: 85.7 },
      { name: '行政管理', count: 152, cumulative: 100.0 },
    ],
  },
  notices: [
    { title: '关于2024届学位论文答辩安排的通知', date: '2024-05-18' },
    { title: '关于学位申请流程优化的通知', date: '2024-05-15' },
    { title: '2024年学位授予条件与要求', date: '2024-05-10' },
    { title: '关于学位论文格式标准的通知', date: '2024-05-08' },
  ],
  todos: [
    { label: '论文评阅审核', count: 12 },
    { label: '答辩安排确认', count: 8 },
    { label: '学位授予审批', count: 5 },
    { label: '学位证书发放', count: 3 },
  ],
}

export const scholarshipMockData = {
  updatedAt: '2024-05-20 10:30:00',
  statCards: [
    { title: '学院奖学金总额', number: 1285.6, unit: '万元', changeLabel: '较上期 ↑8.2%' },
    { title: '学院助学金总额', number: 856.3, unit: '万元', changeLabel: '较上期 ↑6.5%' },
    { title: '学院获奖总人数', number: 2255, unit: '人', changeLabel: '占在读人数 78.4%' },
    { title: '学院获奖人次', number: 1256, unit: '人次', changeLabel: '人均获奖 1.2次' },
    { title: '学院整体获奖率', number: 78.4, unit: '%', changeLabel: '较上期 ↑3.1%' },
  ],
  charts: {
    scholarshipTypes: [
      { name: '国家奖学金', value: 32.3 },
      { name: '学业奖学金', value: 25.3 },
      { name: '社会奖学金', value: 27.9 },
      { name: '其他奖学金', value: 14.5 },
    ],
    aidTypes: [
      { name: '国家助学金', value: 59.8 },
      { name: '临时困难补助', value: 25.4 },
      { name: '其他助学金', value: 14.8 },
    ],
    gradeAwards: [
      { grade: '一年级', national: 202, academic: 185, social: 241 },
      { grade: '二年级', national: 230, academic: 215, social: 267 },
      { grade: '三年级', national: 178, academic: 210, social: 176 },
      { grade: '四年级+', national: 112, academic: 145, social: 94 },
    ],
    studentAwardDistribution: [
      { name: '未获奖', value: 1001, percent: 21.6 },
      { name: '单项奖', value: 1545, percent: 33.4 },
      { name: '多项奖', value: 1709, percent: 37.8 },
    ],
    majorAwardTop: [
      { name: '政治学理论', value: 418, label: '418人(18.5%)' },
      { name: '科学社会主义与国际共产主义运动', value: 356, label: '356人(15.8%)' },
      { name: '中共党史', value: 312, label: '312人(13.8%)' },
      { name: '国际政治', value: 285, label: '285人(12.6%)' },
      { name: '国际关系', value: 267, label: '267人(11.8%)' },
      { name: '其他专业', value: 217, label: '217人(13.5%)' },
    ],
    fundTrend: [
      { year: '2020', value: 1856.2 },
      { year: '2021', value: 1985.5 },
      { year: '2022', value: 2142.8 },
      { year: '2023', value: 2185.6 },
      { year: '2024', value: 2141.9 },
    ],
  },
  notices: [
    { title: '2024年国家奖学金申报通知', date: '2024-05-18' },
    { title: '关于做好学业奖学金评定工作的通知', date: '2024-05-15' },
    { title: '社会奖学金获奖名单公示', date: '2024-05-10' },
    { title: '2024年助学金评定工作启动', date: '2024-05-08' },
  ],
  todos: [
    { label: '奖学金审核', count: 18 },
    { label: '助学金审批', count: 12 },
    { label: '获奖公示确认', count: 7 },
    { label: '证书制作发放', count: 4 },
  ],
}

export const employmentMockData = {
  statCards: [
    { title: '学院就业率', number: 87.9, unit: '%', changeLabel: '较去年 ↑1.2%' },
    { title: '学院签约率', number: 71.5, unit: '%', changeLabel: '较去年 ↑2.3%' },
    { title: '学院升学率', number: 11.3, unit: '%', changeLabel: '较去年 ↑0.8%' },
    { title: '未就业人数', number: 196, unit: '人', changeLabel: '较去年 ↓5人' },
  ],
  metrics: [
    {
      key: 'employment',
      label: '就业率',
      unit: '%',
      series: [
        { year: '2020', value: 82.1 },
        { year: '2021', value: 83.4 },
        { year: '2022', value: 85.2 },
        { year: '2023', value: 86.7 },
        { year: '2024', value: 87.9 },
      ],
    },
    {
      key: 'signing',
      label: '签约率',
      unit: '%',
      series: [
        { year: '2020', value: 63.8 },
        { year: '2021', value: 65.2 },
        { year: '2022', value: 67.1 },
        { year: '2023', value: 69.3 },
        { year: '2024', value: 71.5 },
      ],
    },
    {
      key: 'furtherStudy',
      label: '升学率',
      unit: '%',
      series: [
        { year: '2020', value: 9.1 },
        { year: '2021', value: 9.5 },
        { year: '2022', value: 10.0 },
        { year: '2023', value: 10.7 },
        { year: '2024', value: 11.3 },
      ],
    },
  ],
  charts: {
    unitNature: [
      { name: '民营企业', value: 43.9 },
      { name: '国有企业', value: 30.2 },
      { name: '其他', value: 9.0 },
      { name: '事业单位', value: 7.0 },
      { name: '三资企业', value: 5.5 },
    ],
    industryTop: [
      { name: '软件信息', value: 24.6 },
      { name: '教育', value: 12.2 },
      { name: '制造业', value: 9.7 },
      { name: '公共管理', value: 8.5 },
      { name: '卫生社工', value: 6.3 },
      { name: '文化体育', value: 5.3 },
      { name: '住宿餐饮', value: 2.5 },
    ],
    destinationStats: [
      { type: '签约就业', count: 2031, percent: '71.5%' },
      { type: '升学深造', count: 321, percent: '11.3%' },
      { type: '出国出境', count: 119, percent: '4.2%' },
      { type: '灵活就业', count: 173, percent: '6.1%' },
      { type: '未就业', count: 196, percent: '6.9%' },
    ],
    infoStats: [
      { label: '发布招聘信息', value: '1,246条', valueNum: 1246 },
      { label: '参与招聘活动', value: '632家', valueNum: 632 },
      { label: '举办招聘会', value: '42场', valueNum: 42 },
      { label: '提供岗位', value: '6,762个', valueNum: 6762 },
    ],
    provinceDistribution: [
      { name: '山东', value: 618 },
      { name: '江苏', value: 356 },
      { name: '北京', value: 285 },
      { name: '广东', value: 210 },
      { name: '上海', value: 172 },
      { name: '浙江', value: 146 },
      { name: '四川', value: 118 },
      { name: '湖北', value: 95 },
      { name: '河南', value: 88 },
      { name: '天津', value: 72 },
    ],
  },
}

export const academicChangeMockData = {
  title: '学籍异动管理',
  subtitle: '聚焦异动申请、审批节点与办理时效',
  updatedAt: '2026-05-13 09:10:00',
  primaryAction: { label: '批量审批', message: '批量审批流程已发起' },
  statCards: [
    { title: '待审异动申请', number: 18, icon: 'refresh', changeLabel: '本周新增 6 项' },
    { title: '已办结申请', number: 126, icon: 'check-circle', changeLabel: '办结率 92.6%' },
    { title: '超时未处理', number: 3, icon: 'alert-circle', changeLabel: '需立即跟进' },
    { title: '本月异动人数', number: 28, icon: 'upload', changeLabel: '较上月 +2.0%' },
  ],
  trendChart: {
    title: '近六个月异动申请趋势',
    seriesName: '申请数量',
    unit: '项',
    labels: ['12月', '1月', '2月', '3月', '4月', '5月'],
    values: [12, 16, 11, 18, 22, 28],
    targetName: '目标上限',
    targetValues: [20, 20, 20, 20, 20, 20],
  },
  donutChart: {
    title: '异动类型分布',
    unit: '项',
    centerLabel: '异动总量',
    items: [
      { name: '休学', value: 10 },
      { name: '复学', value: 6 },
      { name: '专业变更', value: 5 },
      { name: '退学', value: 4 },
      { name: '延期毕业', value: 3 },
    ],
  },
  barChart: {
    title: '各专业待办排行',
    unit: '项',
    items: [
      { name: '国际关系', value: 6 },
      { name: '行政管理', value: 5 },
      { name: '政治学理论', value: 4 },
      { name: '国际政治', value: 2 },
      { name: '中共党史', value: 1 },
    ],
  },
  tableCard: {
    title: '异动申请列表',
    columns: [
      { prop: 'studentId', label: '学号', width: 100 },
      { prop: 'name', label: '姓名', width: 70 },
      { prop: 'changeType', label: '异动类型', width: 100 },
      { prop: 'currentStep', label: '当前节点', minWidth: 120 },
      { prop: 'status', label: '状态', width: 90, kind: 'tag' },
      { prop: 'submittedAt', label: '提交时间', width: 110 },
    ],
    rows: [
      { studentId: '20240017', name: '张晨', changeType: '休学', currentStep: '学院审批', status: '待审核', statusType: 'warning', submittedAt: '2026-05-12' },
      { studentId: '20230023', name: '李瑶', changeType: '复学', currentStep: '研究生院复核', status: '流转中', statusType: 'info', submittedAt: '2026-05-11' },
      { studentId: '20220031', name: '赵宁', changeType: '专业变更', currentStep: '导师确认', status: '待补材料', statusType: 'danger', submittedAt: '2026-05-10' },
      { studentId: '20250009', name: '何清', changeType: '延期毕业', currentStep: '学院备案', status: '已办结', statusType: 'success', submittedAt: '2026-05-08' },
    ],
  },
  noticeCard: {
    title: '办理提醒',
    items: [
      { title: '休学申请材料校验截止时间为 5 月 15 日', date: '05-13' },
      { title: '复学学生返校注册名单待确认', date: '05-12' },
      { title: '异动超时工单已自动转入催办池', date: '05-10' },
      { title: '本周专业变更申请需完成导师审核', date: '05-08' },
    ],
  },
  todoCard: {
    title: '审批队列',
    items: [
      { label: '学院初审待处理', count: 7 },
      { label: '导师意见待确认', count: 4 },
      { label: '材料补交流程', count: 3 },
      { label: '超时催办记录', count: 2 },
    ],
  },
}

export const trainingCourseMockData = {
  title: '课程与培养环节管理',
  subtitle: '围绕课程排期、培养节点和过程预警进行统一管理',
  updatedAt: '2026-05-13 09:15:00',
  primaryAction: { label: '同步排课', message: '课程排期同步任务已提交' },
  statCards: [
    { title: '本学期课程数', number: 42, icon: 'book', changeLabel: '覆盖 8 个专业' },
    { title: '待审核教学任务', number: 13, icon: 'shield', changeLabel: '需本周清零' },
    { title: '培养环节预警', number: 9, icon: 'alert-circle', changeLabel: '较上周 +2 项' },
    { title: '课程完成率', number: '84%', icon: 'trend', changeLabel: '较上月 +3.3%' },
  ],
  trendChart: {
    title: '近五周课程执行趋势',
    seriesName: '完成课时',
    unit: '课时',
    labels: ['第1周', '第2周', '第3周', '第4周', '第5周'],
    values: [68, 74, 79, 88, 91],
    targetName: '计划课时',
    targetValues: [72, 72, 78, 84, 90],
  },
  donutChart: {
    title: '培养环节状态分布',
    unit: '项',
    centerLabel: '当前环节',
    items: [
      { name: '课程学习', value: 15 },
      { name: '开题准备', value: 8 },
      { name: '中期考核', value: 6 },
      { name: '答辩阶段', value: 4 },
    ],
  },
  barChart: {
    title: '课程负载 TOP5',
    unit: '门',
    items: [
      { name: '政治学理论', value: 9 },
      { name: '行政管理', value: 8 },
      { name: '国际关系', value: 7 },
      { name: '国际政治', value: 6 },
      { name: '统一战线学', value: 5 },
    ],
  },
  tableCard: {
    title: '课程执行清单',
    columns: [
      { prop: 'courseName', label: '课程名称', minWidth: 150 },
      { prop: 'teacher', label: '任课教师', width: 90 },
      { prop: 'major', label: '开课专业', minWidth: 120 },
      { prop: 'schedule', label: '排期', width: 120 },
      { prop: 'status', label: '状态', width: 90, kind: 'tag' },
    ],
    rows: [
      { courseName: '政治学研究方法', teacher: '刘老师', major: '政治学理论', schedule: '周二 3-4 节', status: '已发布', statusType: 'success' },
      { courseName: '公共政策分析', teacher: '周老师', major: '行政管理', schedule: '周三 1-2 节', status: '待排课', statusType: 'warning' },
      { courseName: '国际关系理论专题', teacher: '黄老师', major: '国际关系', schedule: '周四 5-6 节', status: '待审核', statusType: 'info' },
      { courseName: '统一战线理论前沿', teacher: '许老师', major: '统一战线学', schedule: '周五 1-2 节', status: '需调整', statusType: 'danger' },
    ],
  },
  noticeCard: {
    title: '教学通知',
    items: [
      { title: '下周排课变更需在今晚 20:00 前确认', date: '05-13' },
      { title: '开题环节材料审核截止时间更新', date: '05-12' },
      { title: '中期考核模板已同步至培养资料库', date: '05-10' },
      { title: '课程成绩异常名单待教秘核验', date: '05-08' },
    ],
  },
  todoCard: {
    title: '本周待办',
    items: [
      { label: '待排课任务', count: 6 },
      { label: '教学任务待审核', count: 5 },
      { label: '开题材料待补交', count: 4 },
      { label: '课程冲突待协调', count: 2 },
    ],
  },
}

export const degreeDefenseMockData = {
  title: '答辩管理',
  subtitle: '统一管理答辩场次、专家安排和结果回收',
  updatedAt: '2026-05-13 09:20:00',
  primaryAction: { label: '生成会场安排', message: '答辩会场安排已生成' },
  statCards: [
    { title: '待答辩学生', number: 86, icon: 'graduation', changeLabel: '本周新增 9 人' },
    { title: '已排场次', number: 24, icon: 'clock', changeLabel: '覆盖 5 个会场' },
    { title: '专家待确认', number: 11, icon: 'users', changeLabel: '需尽快完成回执' },
    { title: '材料待回收', number: 7, icon: 'file', changeLabel: '答辩后 24h 内归档' },
  ],
  trendChart: {
    title: '本周答辩排期趋势',
    seriesName: '排定人数',
    unit: '人',
    labels: ['周一', '周二', '周三', '周四', '周五'],
    values: [12, 18, 20, 16, 20],
    targetName: '计划人数',
    targetValues: [15, 18, 18, 18, 17],
  },
  donutChart: {
    title: '答辩准备分布',
    unit: '人',
    centerLabel: '答辩准备',
    items: [
      { name: '材料完备', value: 48 },
      { name: '待导师确认', value: 18 },
      { name: '待专家确认', value: 11 },
      { name: '待补交附件', value: 9 },
    ],
  },
  barChart: {
    title: '会场使用频次',
    unit: '场',
    items: [
      { name: '文澜楼 A201', value: 8 },
      { name: '文澜楼 A305', value: 6 },
      { name: '知新楼 1208', value: 4 },
      { name: '知新楼 1210', value: 3 },
      { name: '图西报告厅', value: 3 },
    ],
  },
  tableCard: {
    title: '答辩场次安排',
    columns: [
      { prop: 'sessionName', label: '场次', minWidth: 140 },
      { prop: 'chair', label: '主席', width: 90 },
      { prop: 'room', label: '会场', minWidth: 120 },
      { prop: 'students', label: '学生数', width: 80 },
      { prop: 'status', label: '状态', width: 90, kind: 'tag' },
      { prop: 'time', label: '时间', width: 120 },
    ],
    rows: [
      { sessionName: '政治学理论第一组', chair: '陈老师', room: '文澜楼 A201', students: 6, status: '已确认', statusType: 'success', time: '05-15 09:00' },
      { sessionName: '国际关系第二组', chair: '李老师', room: '文澜楼 A305', students: 5, status: '待确认', statusType: 'warning', time: '05-15 14:30' },
      { sessionName: '行政管理专场', chair: '王老师', room: '知新楼 1208', students: 4, status: '待材料', statusType: 'danger', time: '05-16 09:00' },
      { sessionName: '统一战线学专场', chair: '周老师', room: '图西报告厅', students: 3, status: '流转中', statusType: 'info', time: '05-16 15:00' },
    ],
  },
  noticeCard: {
    title: '答辩通知',
    items: [
      { title: '专家回执未提交名单已发送提醒', date: '05-13' },
      { title: '答辩材料归档模板已更新', date: '05-12' },
      { title: '行政管理专场会场调整至知新楼 1208', date: '05-10' },
      { title: '本周答辩录像存档路径已开放', date: '05-09' },
    ],
  },
  todoCard: {
    title: '关键待办',
    items: [
      { label: '专家回执待确认', count: 5 },
      { label: '会场物料待准备', count: 4 },
      { label: '答辩材料待补交', count: 3 },
      { label: '结果单待上传', count: 2 },
    ],
  },
}

const intelligentPredictionRadarIndicators = [
  { name: '课程成绩', max: 120 },
  { name: '科研投入', max: 120 },
  { name: '活动参与', max: 120 },
  { name: '社会实践', max: 120 },
  { name: '导师评价', max: 120 },
  { name: '出勤纪律', max: 120 },
  { name: '心理健康', max: 120 },
]

const predictionMonths = ['2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06', '2025-07', '2025-08', '2025-09']
const predictionStudentNames = [
  '张浩然',
  '李思琪',
  '王博文',
  '刘雅琪',
  '陈嘉欣',
  '赵子轩',
  '孙雨萱',
  '周俊豪',
  '吴佳怡',
  '郑子涵',
  '黄思远',
  '林雨桐',
  '何晨曦',
  '马一帆',
  '罗安琪',
  '高宇航',
  '梁欣怡',
  '谢知远',
  '宋可欣',
  '唐俊熙',
  '许清妍',
  '邓浩宇',
  '韩书瑶',
  '曹景行',
  '曾语涵',
  '彭明轩',
  '肖可心',
  '田子墨',
  '董诗雨',
  '袁博雅',
]
const predictionSuggestions = {
  学业风险: '建议优先补强课程学习、学分推进与阶段学业督导',
  培养风险: '建议复核培养节点任务并建立周度督办节奏',
  科研风险: '建议细化科研任务安排并强化项目参与和成果产出',
  支持风险: '建议增加导师沟通频次并同步开展支持服务跟进',
}

function predictionClamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function predictionRound(value) {
  return Number(value.toFixed(1))
}

function buildPredictionSeries(target, spread, seed, options = {}) {
  const { min = 0, max = 100, integer = false } = options
  const startValue = Math.max(min, target - spread)
  return predictionMonths.map((_, index) => {
    const progress = index / Math.max(predictionMonths.length - 1, 1)
    const base = startValue + ((target - startValue) * progress)
    const jitter = (((seed + index) % 3) - 1) * (integer ? 1 : 0.6)
    const value = predictionClamp(index === predictionMonths.length - 1 ? target : base + jitter, min, max)
    return integer ? Math.round(value) : predictionRound(value)
  })
}

function buildPredictionStudentPlacement(index) {
  const pairSize = 2
  const comboIndex = Math.floor(index / pairSize)
  const gradeCount = sharedOptions.grades.length
  const degreeTypes = sharedOptions.degreeTypes
  const gradeIndex = comboIndex % gradeCount
  const degreeIndex = Math.floor(comboIndex / gradeCount) % degreeTypes.length
  const majorIndex = (comboIndex * 2) % sharedOptions.majors.length

  return {
    comboIndex,
    gradeIndex,
    degreeIndex,
    majorIndex,
    degreeType: degreeTypes[degreeIndex],
  }
}

function buildPredictionCurrentSnapshot(studentIndex, majorIndex, gradeIndex, degreeType) {
  const stageDepth = Math.max(0, sharedOptions.grades.length - gradeIndex - 1)
  const degreeBonus = degreeType === '博士' ? 5 : 0
  const professionalOffset = degreeType === '专业型硕士' ? -1 : 0

  return {
    courseAverage: predictionRound(predictionClamp(76 + stageDepth * 1.7 + (majorIndex % 4) * 1.8 + (studentIndex % 5) + degreeBonus + professionalOffset, 68, 96)),
    creditCompletionRate: predictionRound(predictionClamp(58 + stageDepth * 8.5 + (studentIndex % 10) * 1.6, 42, 100)),
    attendanceRate: predictionRound(predictionClamp(87 + (studentIndex % 7) + (majorIndex % 2), 78, 99)),
    researchTaskCompletionRate: predictionRound(predictionClamp(46 + stageDepth * 7.2 + (majorIndex % 5) * 1.5 + (degreeType === '博士' ? 8 : 0), 35, 98)),
    researchOutputCount: Math.max(0, Math.min(5, (studentIndex % 3) + (degreeType === '博士' ? 1 : 0))),
    projectParticipationCount: Math.max(1, Math.min(4, 1 + ((studentIndex + majorIndex) % 4))),
    activityHours: Math.max(6, Math.min(24, 8 + stageDepth * 2 + (studentIndex % 6))),
    activityCount: Math.max(1, Math.min(6, 2 + ((studentIndex + gradeIndex) % 4))),
    practiceHours: Math.max(3, Math.min(26, 5 + stageDepth * 2 + (studentIndex % 7))),
    practiceReportCount: Math.max(1, Math.min(4, 1 + (stageDepth >= 2 ? 1 : 0) + (studentIndex % 2))),
    advisorEvaluationScore: predictionRound(predictionClamp(74 + stageDepth * 1.5 + ((studentIndex + majorIndex) % 8) + (degreeType === '博士' ? 2 : 0), 68, 95)),
    advisorMeetingCount60d: Math.max(1, Math.min(5, 2 + ((studentIndex + gradeIndex) % 4))),
    advisorAvgResponseDays: Math.max(2, Math.min(10, 9 - (2 + ((studentIndex + gradeIndex) % 4)) + (studentIndex % 3))),
    missedCheckins: Math.max(0, Math.min(4, (studentIndex + majorIndex) % 4)),
    wellbeingScore: predictionRound(predictionClamp(77 + (studentIndex % 9) + (gradeIndex % 3), 72, 95)),
    trainingPlanCompletionRate: predictionRound(predictionClamp(55 + stageDepth * 9 + (studentIndex % 8) * 1.8, 38, 100)),
    graduationProgressRate: predictionRound(predictionClamp(42 + stageDepth * 10.5 + (studentIndex % 7) * 1.6 + degreeBonus, 28, 100)),
    overdueTasksCount: Math.max(0, Math.min(5, 4 - Math.min(stageDepth, 3) + (studentIndex % 2))),
  }
}

function buildPredictionMonthlyMetrics(snapshot, studentIndex) {
  return {
    months: predictionMonths,
    courseAverage: buildPredictionSeries(snapshot.courseAverage, 8 + (studentIndex % 3), studentIndex + 11),
    creditCompletionRate: buildPredictionSeries(snapshot.creditCompletionRate, 18 + (studentIndex % 5), studentIndex + 13),
    attendanceRate: buildPredictionSeries(snapshot.attendanceRate, 6, studentIndex + 17),
    researchTaskCompletionRate: buildPredictionSeries(snapshot.researchTaskCompletionRate, 16 + (studentIndex % 4), studentIndex + 19),
    activityHours: buildPredictionSeries(snapshot.activityHours, 5, studentIndex + 23, { min: 0, max: 30, integer: true }),
    practiceHours: buildPredictionSeries(snapshot.practiceHours, 4, studentIndex + 29, { min: 0, max: 30, integer: true }),
    advisorMeetingCount: buildPredictionSeries(snapshot.advisorMeetingCount60d, 2, studentIndex + 31, { min: 1, max: 6, integer: true }),
    advisorEvaluationScore: buildPredictionSeries(snapshot.advisorEvaluationScore, 7, studentIndex + 37),
    wellbeingScore: buildPredictionSeries(snapshot.wellbeingScore, 6, studentIndex + 41),
  }
}

function buildPredictionRiskProfile(snapshot) {
  const categoryScores = [
    {
      category: '学业风险',
      field: '课程成绩与学分完成',
      score: Math.max(0, 82 - snapshot.courseAverage) * 0.9 + Math.max(0, 80 - snapshot.creditCompletionRate) * 0.8,
    },
    {
      category: '培养风险',
      field: '培养计划与毕业进度',
      score: Math.max(0, 82 - snapshot.trainingPlanCompletionRate) * 0.8 + Math.max(0, 78 - snapshot.graduationProgressRate) * 0.7 + snapshot.overdueTasksCount * 2.2,
    },
    {
      category: '科研风险',
      field: '科研任务与成果产出',
      score: Math.max(0, 78 - snapshot.researchTaskCompletionRate) * 0.85 + Math.max(0, 2 - snapshot.researchOutputCount) * 4.6,
    },
    {
      category: '支持风险',
      field: '导师支持与身心状态',
      score: Math.max(0, snapshot.advisorAvgResponseDays - 5) * 3.2 + Math.max(0, 84 - snapshot.wellbeingScore) * 0.7 + Math.max(0, 3 - snapshot.advisorMeetingCount60d) * 3.5,
    },
  ].sort((left, right) => right.score - left.score)

  const [topCategory, secondCategory] = categoryScores
  const riskScore = predictionRound((topCategory.score * 0.65) + ((secondCategory?.score || 0) * 0.35))
  let riskLevel = '低风险'
  let riskType = 'success'

  if (riskScore >= 28) {
    riskLevel = '高风险'
    riskType = 'danger'
  } else if (riskScore >= 18) {
    riskLevel = '预警'
    riskType = 'warning'
  }

  const riskField = [topCategory?.field, secondCategory?.field]
    .filter((item, index, array) => item && array.indexOf(item) === index)
    .join('、')

  return {
    riskScore,
    riskCategory: topCategory?.category || '培养风险',
    riskLevel,
    riskType,
    riskField,
    suggestion: predictionSuggestions[topCategory?.category] || '建议持续跟踪并在月度节点复核',
  }
}

function predictionCompositeIndex(student) {
  const snapshot = student.currentSnapshot
  return predictionRound(
    (snapshot.courseAverage * 0.2) +
    (snapshot.creditCompletionRate * 0.16) +
    (snapshot.researchTaskCompletionRate * 0.17) +
    (snapshot.attendanceRate * 0.1) +
    (snapshot.trainingPlanCompletionRate * 0.14) +
    (snapshot.graduationProgressRate * 0.11) +
    (snapshot.advisorEvaluationScore * 0.07) +
    (snapshot.wellbeingScore * 0.05),
  )
}

function predictionMonthlyIndex(student, index) {
  const metrics = student.monthlyMetrics
  return predictionRound(
    (metrics.courseAverage[index] * 0.24) +
    (metrics.creditCompletionRate[index] * 0.18) +
    (metrics.researchTaskCompletionRate[index] * 0.17) +
    (metrics.attendanceRate[index] * 0.12) +
    (metrics.advisorEvaluationScore[index] * 0.11) +
    (metrics.wellbeingScore[index] * 0.1) +
    (metrics.activityHours[index] * 1.2) +
    (metrics.practiceHours[index] * 0.9),
  )
}

function buildPredictionMonthlyRecords(metrics) {
  return (metrics.months || []).map((month, index) => ({
    month,
    courseAverage: Number(metrics.courseAverage?.[index] || 0),
    creditCompletionRate: Number(metrics.creditCompletionRate?.[index] || 0),
    attendanceRate: Number(metrics.attendanceRate?.[index] || 0),
    researchTaskCompletionRate: Number(metrics.researchTaskCompletionRate?.[index] || 0),
    activityHours: Number(metrics.activityHours?.[index] || 0),
    practiceHours: Number(metrics.practiceHours?.[index] || 0),
    advisorMeetingCount: Number(metrics.advisorMeetingCount?.[index] || 0),
    advisorEvaluationScore: Number(metrics.advisorEvaluationScore?.[index] || 0),
    wellbeingScore: Number(metrics.wellbeingScore?.[index] || 0),
  }))
}

function predictionScaleScore(snapshot, key, maximum) {
  const value = Number(snapshot?.[key] || 0)
  if (maximum <= 0) return 0
  return predictionClamp((value / maximum) * 100, 0, 100)
}

function predictionReverseScaleScore(snapshot, key, maximum) {
  const value = Number(snapshot?.[key] || 0)
  if (maximum <= 0) return 0
  return predictionClamp(100 - ((value / maximum) * 100), 0, 100)
}

function predictionWeightedScore(parts) {
  const totalWeight = parts.reduce((sum, [weight]) => sum + weight, 0) || 1
  const weighted = parts.reduce((sum, [weight, score]) => sum + (weight * predictionClamp(Number(score || 0), 0, 100)), 0)
  return predictionRound(weighted / totalWeight)
}

function buildPredictionRadar(snapshot) {
  return [
    predictionWeightedScore([
      [0.40, snapshot.courseAverage],
      [0.30, snapshot.creditCompletionRate],
      [0.15, snapshot.trainingPlanCompletionRate],
      [0.15, snapshot.graduationProgressRate],
    ]),
    predictionWeightedScore([
      [0.40, snapshot.researchTaskCompletionRate],
      [0.25, predictionScaleScore(snapshot, 'researchOutputCount', 4)],
      [0.20, predictionScaleScore(snapshot, 'projectParticipationCount', 4)],
      [0.15, snapshot.graduationProgressRate],
    ]),
    predictionWeightedScore([
      [0.40, snapshot.attendanceRate],
      [0.30, predictionReverseScaleScore(snapshot, 'missedCheckins', 5)],
      [0.20, predictionReverseScaleScore(snapshot, 'overdueTasksCount', 6)],
      [0.10, snapshot.creditCompletionRate],
    ]),
    predictionWeightedScore([
      [0.50, snapshot.advisorEvaluationScore],
      [0.30, predictionScaleScore(snapshot, 'advisorMeetingCount60d', 5)],
      [0.20, predictionReverseScaleScore(snapshot, 'advisorAvgResponseDays', 10)],
    ]),
    predictionWeightedScore([
      [0.35, predictionScaleScore(snapshot, 'activityHours', 30)],
      [0.25, predictionScaleScore(snapshot, 'activityCount', 6)],
      [0.20, predictionScaleScore(snapshot, 'projectParticipationCount', 4)],
      [0.20, predictionScaleScore(snapshot, 'advisorMeetingCount60d', 5)],
    ]),
    predictionWeightedScore([
      [0.50, predictionScaleScore(snapshot, 'practiceHours', 30)],
      [0.30, predictionScaleScore(snapshot, 'practiceReportCount', 4)],
      [0.20, predictionScaleScore(snapshot, 'activityCount', 6)],
    ]),
    predictionWeightedScore([
      [0.60, snapshot.wellbeingScore],
      [0.20, predictionReverseScaleScore(snapshot, 'missedCheckins', 5)],
      [0.20, predictionReverseScaleScore(snapshot, 'overdueTasksCount', 6)],
    ]),
  ]
}

function buildPredictionHistoricalForecast(actualSeries) {
  if (!actualSeries.length) return []
  const startIndex = Math.max(2, actualSeries.length - 4)
  return actualSeries.map((_, index) => {
    if (index < startIndex) return null
    const base = actualSeries[index - 1] ?? actualSeries[index]
    const prev = actualSeries[Math.max(0, index - 2)] ?? base
    return predictionRound(predictionClamp(base + ((base - prev) * 0.8), 0, 100))
  })
}

function buildPredictionProjection(actualSeries, mode = 'trend') {
  if (!actualSeries.length) return [0, 0, 0, 0]
  const recent = actualSeries.slice(-4)
  const current = recent[recent.length - 1]
  const slope = recent.length > 1 ? (recent[recent.length - 1] - recent[0]) / (recent.length - 1) : 0
  const factor = mode === 'scenario' ? 0.6 : 1
  return [0, 1, 2, 3].map((step) => predictionRound(predictionClamp(current + (slope * factor * step), 0, 100)))
}

function buildPredictionUpperProjection(baseSeries, padding = 3.5) {
  return baseSeries.map((value, index) => predictionRound(predictionClamp(Number(value || 0) + padding + (index * 1.2), 0, 100)))
}

function buildPredictionFactors(radarValues) {
  const deficitItems = [
    { label: '学业投入与掌握', gap: 100 - Number(radarValues[0] || 0) },
    { label: '科研训练与创新', gap: 100 - Number(radarValues[1] || 0) },
    { label: '自我管理与学习策略', gap: 100 - Number(radarValues[2] || 0) },
    { label: '导师支持与学术互动', gap: 100 - Number(radarValues[3] || 0) },
    { label: '学术共同体融入', gap: 100 - Number(radarValues[4] || 0) },
    { label: '实践参与与公共服务', gap: 100 - Number(radarValues[5] || 0) },
    { label: '身心健康与持续发展', gap: 100 - Number(radarValues[6] || 0) },
  ]
    .map((item) => ({ ...item, gap: predictionRound(predictionClamp(item.gap, 0, 100)) }))
    .sort((left, right) => right.gap - left.gap)
    .slice(0, 5)

  const totalGap = deficitItems.reduce((sum, item) => sum + item.gap, 0) || 1
  return deficitItems.map((item) => ({
    label: item.label,
    value: `${predictionRound((item.gap * 100) / totalGap)}%`,
    gap: item.gap,
  }))
}

function buildPredictionGauges(snapshot, riskScore) {
  return {
    graduation: predictionRound(predictionClamp(100 - Number(snapshot.graduationProgressRate || 0), 0, 100)),
    training: predictionRound(predictionClamp(100 - Number(snapshot.trainingPlanCompletionRate || 0), 0, 100)),
    feedback: predictionRound(predictionClamp(Number(snapshot.advisorAvgResponseDays || 0) * 8, 0, 100)),
    risk: predictionRound(predictionClamp(Number(riskScore || 0) * 2.2, 0, 100)),
  }
}

function formatPredictionSeriesText(values) {
  return (values || []).map((value) => (value === null ? 'null' : String(value))).join('|')
}

function formatPredictionFactorsText(factors) {
  return (factors || [])
    .filter((item) => item?.label)
    .map((item) => `${item.label}=${item.value}`)
    .join(' | ')
}

function createPredictionStudent(name, index) {
  const placement = buildPredictionStudentPlacement(index)
  const majorIndex = placement.majorIndex
  const gradeIndex = placement.gradeIndex
  const major = sharedOptions.majors[majorIndex]
  const grade = sharedOptions.grades[gradeIndex]
  const degreeType = placement.degreeType
  const advisorName = ['王教授', '李教授', '张教授', '刘教授', '陈教授', '赵教授', '孙教授', '周教授'][majorIndex]
  const studentId = `${grade.slice(0, 4)}${String(majorIndex + 1).padStart(2, '0')}${String(index + 1).padStart(4, '0')}`
  const currentSnapshot = buildPredictionCurrentSnapshot(index, majorIndex, gradeIndex, degreeType)
  const monthlyMetrics = buildPredictionMonthlyMetrics(currentSnapshot, index)
  const riskProfile = buildPredictionRiskProfile(currentSnapshot)

  return {
    id: `stu-${studentId}`,
    studentId,
    name,
    degreeType,
    college: '政治学与公共管理学院',
    advisorName,
    major,
    grade,
    type: degreeType,
    tagType: riskProfile.riskType,
    ...riskProfile,
    summary: `${grade}${major}样本当前主要关注 ${riskProfile.riskField}，建议围绕 ${riskProfile.riskCategory} 做连续干预。`,
    aiConclusion: `${grade}${major}样本当前主要关注 ${riskProfile.riskField}，建议围绕 ${riskProfile.riskCategory} 做连续干预。`,
    currentSnapshot,
    monthlyMetrics,
    period: '未来 3 个月',
  }
}

function enrichPredictionStudent(student, students) {
  const monthlyRecords = buildPredictionMonthlyRecords(student.monthlyMetrics)
  const radar = buildPredictionRadar(student.currentSnapshot)
  const trendActual = predictionMonths.map((_, index) => predictionMonthlyIndex(student, index))
  const trendForecast = buildPredictionHistoricalForecast(trendActual)
  const peers = students.filter((item) => item.grade === student.grade)
  const peerTrend = predictionMonths.map((_, index) => {
    const values = peers
      .map((item) => predictionMonthlyIndex(item, index))
      .filter((value) => Number.isFinite(value))
    if (!values.length) return null
    return predictionRound(values.reduce((sum, value) => sum + value, 0) / values.length)
  })
  const forecastTrend = buildPredictionProjection(trendActual, 'trend')
  const forecastScenario = buildPredictionProjection(trendActual, 'scenario')
  const forecastUpperTrend = buildPredictionUpperProjection(forecastTrend, 3.5)
  const forecastUpperScenario = buildPredictionUpperProjection(forecastScenario, 2.8)
  const factors = buildPredictionFactors(radar)
  const gauges = buildPredictionGauges(student.currentSnapshot, student.riskScore)

  return {
    ...student,
    monthlyRecords,
    radar,
    radarValues: radar,
    trendActual,
    historicalTrend: trendActual,
    trendForecast,
    predictedTrend: trendForecast,
    peerTrend,
    peerAverageTrend: peerTrend,
    forecastTrend,
    forecastTrendValues: forecastTrend,
    forecastScenario,
    scenarioValues: forecastScenario,
    forecastUpperTrend,
    trendUpperBound: forecastUpperTrend,
    forecastUpperScenario,
    scenarioUpperBound: forecastUpperScenario,
    factors,
    keyFactors: factors,
    keyFactorsText: formatPredictionFactorsText(factors),
    gauges,
    graduationWarning: gauges.graduation,
    trainingLag: gauges.training,
    feedbackDelay: gauges.feedback,
    riskRate: gauges.risk,
    historicalTrendText: formatPredictionSeriesText(trendActual),
    predictedTrendText: formatPredictionSeriesText(trendForecast),
    peerAverageTrendText: formatPredictionSeriesText(peerTrend),
    radarValuesText: formatPredictionSeriesText(radar),
    forecastTrendValuesText: formatPredictionSeriesText(forecastTrend),
    scenarioValuesText: formatPredictionSeriesText(forecastScenario),
    trendUpperBoundText: formatPredictionSeriesText(forecastUpperTrend),
    scenarioUpperBoundText: formatPredictionSeriesText(forecastUpperScenario),
  }
}

function predictionRiskPriority(type) {
  return { danger: 3, warning: 2, info: 1, success: 0 }[type] ?? 0
}

const intelligentPredictionStudents = predictionStudentNames
  .map((name, index) => createPredictionStudent(name, index))
  .map((student, _, students) => enrichPredictionStudent(student, students))
const intelligentPredictionRiskRows = intelligentPredictionStudents
  .map((student) => ({
    studentId: student.studentId,
    name: student.name,
    grade: student.grade,
    major: student.major,
    college: student.college,
    riskScore: student.riskScore,
    riskCategory: student.riskCategory,
    riskLevel: student.riskLevel,
    riskType: student.riskType,
    riskField: student.riskField,
    suggestion: student.suggestion,
  }))
  .sort((left, right) => {
    const typeGap = predictionRiskPriority(right.riskType) - predictionRiskPriority(left.riskType)
    if (typeGap !== 0) return typeGap
    return Number(right.riskScore || 0) - Number(left.riskScore || 0)
  })

const predictionHighRiskCount = intelligentPredictionStudents.filter((student) => student.riskLevel === '高风险').length
const predictionAlertCount = intelligentPredictionStudents.filter((student) => ['高风险', '预警'].includes(student.riskLevel)).length
const predictionAverageIndex = predictionRound(
  intelligentPredictionStudents.reduce((sum, student) => sum + predictionCompositeIndex(student), 0)
  / Math.max(intelligentPredictionStudents.length, 1),
)
const predictionDelayedFeedbackRate = predictionRound(
  intelligentPredictionStudents.filter((student) => student.currentSnapshot.advisorAvgResponseDays >= 8).length * 100
  / Math.max(intelligentPredictionStudents.length, 1),
)
const predictionTrendLabels = predictionMonths.slice(-6)
const predictionTrendValues = predictionTrendLabels.map((_, index) => predictionRound(
  intelligentPredictionStudents.reduce((sum, student) => sum + predictionMonthlyIndex(student, index + 3), 0)
  / Math.max(intelligentPredictionStudents.length, 1),
))
const predictionPeerTrendValues = predictionTrendLabels.map((_, index) => {
  const peers = intelligentPredictionStudents.filter((student) => student.grade === '2023级')
  return predictionRound(
    peers.reduce((sum, student) => sum + predictionMonthlyIndex(student, index + 3), 0)
    / Math.max(peers.length, 1),
  )
})
const predictionFactorCounter = intelligentPredictionRiskRows.reduce((counter, row) => {
  row.riskField.split('、').forEach((field) => {
    const name = field.trim()
    if (!name) return
    counter[name] = (counter[name] || 0) + 1
  })
  return counter
}, {})
const predictionFactorItems = Object.entries(predictionFactorCounter)
  .sort((left, right) => right[1] - left[1])
  .slice(0, 5)
  .map(([name, count]) => ({
    name,
    value: predictionRound((count * 100) / Math.max(intelligentPredictionStudents.length, 1)),
  }))

export const intelligentPredictionMockData = {
  title: '智能预测与预警',
  subtitle: '基于 2021级至2025级模拟研究生样本，开展趋势预测、风险解读与治理支持',
  businessScope: {
    university: '山东大学',
    college: '政治学与公共管理学院',
    audience: '山东大学政治学与公共管理学院研究生',
  },
  updatedAt: '2026-06-21 12:00:00',
  aiCapabilities: {
    llmEnabled: true,
    provider: 'deepseek',
    apiStyle: 'chat_completions',
    model: 'deepseek-v4-pro',
    chatMode: 'llm',
    retrievalEnabled: true,
    debugEnabled: false,
    runtimeOptions: {
      supportsPreferredModel: true,
      supportsApiStyle: true,
      supportsThinkingType: true,
      supportsReasoningEffort: true,
      supportsTemperature: true,
      supportsUseLlmWhenAvailable: true,
    },
    endpoints: {
      context: '/api/v1/intelligent-prediction/context/',
      analyze: '/api/v1/intelligent-prediction/analyze/',
      chat: '/api/v1/intelligent-prediction/chat/',
    },
  },
  filters: {
    default: {
      college: '政治学与公共管理学院',
      major: '全部专业',
      grade: '2023级',
      range: '近6个月',
      riskType: '全部',
    },
    colleges: ['政治学与公共管理学院'],
    majors: ['全部专业', ...sharedOptions.majors],
    grades: ['全部年级', ...sharedOptions.grades],
    ranges: ['近3个月', '近6个月', '近9个月'],
    riskTypes: ['全部', '学业风险', '培养风险', '科研风险', '支持风险'],
  },
  radarIndicators: intelligentPredictionRadarIndicators,
  students: intelligentPredictionStudents,
  riskStudents: intelligentPredictionRiskRows,
  primaryAction: { label: '刷新预测', message: '预测分析结果已刷新' },
  statCards: [
    { title: '高风险学生', number: predictionHighRiskCount, icon: 'alert-circle', changeLabel: '当前模拟样本中重点干预对象' },
    { title: '预警关注学生', number: predictionAlertCount, icon: 'shield', changeLabel: '当前模拟样本中需持续跟踪' },
    { title: '平均发展指数', number: predictionAverageIndex, icon: 'trend', changeLabel: `按 ${intelligentPredictionStudents.length} 个模拟样本测算` },
    { title: '导师反馈延迟率', number: `${predictionDelayedFeedbackRate}%`, icon: 'clock', changeLabel: '反馈类风险占比较高' },
  ],
  trendChart: {
    title: '模拟学生发展趋势分析',
    seriesName: '综合发展指数',
    unit: '分',
    labels: predictionTrendLabels,
    values: predictionTrendValues,
    targetName: '同年级平均',
    targetValues: predictionPeerTrendValues,
  },
  donutChart: {
    title: '风险等级分布',
    unit: '人',
    centerLabel: '预警总人数',
    items: [
      { name: '高风险', value: predictionHighRiskCount, color: '#F53F3F' },
      { name: '预警', value: predictionAlertCount - predictionHighRiskCount, color: '#FA8C16' },
      { name: '低风险', value: intelligentPredictionStudents.length - predictionAlertCount, color: '#165DFF' },
    ],
  },
  barChart: {
    title: '关键影响因素 TOP5',
    unit: '%',
    items: predictionFactorItems,
  },
  tableCard: {
    title: '高风险学生 TOP5',
    columns: [
      { prop: 'studentId', label: '学号', width: 110 },
      { prop: 'name', label: '姓名', width: 80 },
      { prop: 'riskLevel', label: '风险等级', width: 100, kind: 'tag', typeField: 'riskType' },
      { prop: 'riskField', label: '主要风险领域', minWidth: 130 },
      { prop: 'suggestion', label: '建议动作', minWidth: 140 },
    ],
    rows: intelligentPredictionRiskRows.slice(0, 5),
  },
  noticeCard: {
    title: 'AI 预警提示',
    items: [
      { title: '近 6 个月学生整体发展指数稳步上升，未来 3 个月预计维持增长趋势', date: '11:20' },
      { title: '课程完成率和科研投入是当前影响发展指数的两项核心因素', date: '11:05' },
      { title: '部分学生在培养计划滞后和导师反馈延迟问题上需重点关注', date: '10:42' },
      { title: '建议对连续 2 周高风险学生启动一对一跟踪机制', date: '10:18' },
    ],
  },
  todoCard: {
    title: '模型与治理待办',
    items: [
      { label: '待复核高风险学生', count: predictionHighRiskCount },
      { label: '待更新预测样本', count: intelligentPredictionStudents.filter((student) => student.currentSnapshot.trainingPlanCompletionRate < 70).length },
      { label: '待补录导师反馈', count: intelligentPredictionStudents.filter((student) => student.currentSnapshot.advisorMeetingCount60d <= 2).length },
      { label: '待导出周报', count: 2 },
    ],
  },
}

export const systemSettingsMockData = {
  title: '系统设置',
  subtitle: '维护系统参数、开放时间和消息通知策略',
  updatedAt: '2026-05-13 09:40:00',
  primaryAction: { label: '保存配置', message: '系统配置已保存' },
  statCards: [
    { title: '启用参数项', number: 36, icon: 'shield', changeLabel: '当前启用率 94%' },
    { title: '消息模板数', number: 18, icon: 'send', changeLabel: '覆盖 7 类业务' },
    { title: '开放时间策略', number: 9, icon: 'clock', changeLabel: '含 3 个临时策略' },
    { title: '待发布配置', number: 4, icon: 'layers', changeLabel: '需管理员确认' },
  ],
  trendChart: {
    title: '近五次配置变更趋势',
    seriesName: '变更数量',
    unit: '项',
    labels: ['04-20', '04-27', '05-04', '05-10', '05-13'],
    values: [6, 4, 8, 5, 7],
    targetName: '建议阈值',
    targetValues: [6, 6, 6, 6, 6],
  },
  donutChart: {
    title: '配置类别占比',
    unit: '项',
    centerLabel: '配置总量',
    items: [
      { name: '业务参数', value: 14 },
      { name: '消息通知', value: 9 },
      { name: '开放时间', value: 7 },
      { name: '数据同步', value: 6 },
    ],
  },
  barChart: {
    title: '近月高频修改项',
    unit: '次',
    items: [
      { name: '培养流程开放时间', value: 7 },
      { name: '奖助通知模板', value: 6 },
      { name: '答辩材料清单', value: 5 },
      { name: '招生口径参数', value: 4 },
      { name: '首页卡片展示项', value: 3 },
    ],
  },
  tableCard: {
    title: '系统配置清单',
    columns: [
      { prop: 'item', label: '配置项', minWidth: 170 },
      { prop: 'module', label: '所属模块', width: 110 },
      { prop: 'owner', label: '维护人', width: 80 },
      { prop: 'status', label: '状态', width: 90, kind: 'tag' },
      { prop: 'updatedAt', label: '更新时间', width: 110 },
    ],
    rows: [
      { item: '数据上传与导入管理', module: '数据管理', owner: '系统', status: '已生效', statusType: 'success', updatedAt: '2026-05-13', action: '/data-management' },
      { item: '数据导出与模板管理', module: '数据管理', owner: '系统', status: '已生效', statusType: 'success', updatedAt: '2026-05-13', action: '/data-management' },
      { item: '培养计划提交截止时间', module: '培养管理', owner: '张老师', status: '已生效', statusType: 'success', updatedAt: '2026-05-13' },
      { item: '答辩通知短信模板', module: '学位管理', owner: '李老师', status: '待发布', statusType: 'warning', updatedAt: '2026-05-12' },
      { item: '首页统计口径映射', module: '首页', owner: '王老师', status: '审核中', statusType: 'info', updatedAt: '2026-05-11' },
      { item: '奖学金批次配置', module: '奖助管理', owner: '周老师', status: '需修订', statusType: 'danger', updatedAt: '2026-05-10' },
    ],
  },
  noticeCard: {
    title: '配置通知',
    items: [
      { title: '今晚 22:00 将发布新一版消息模板', date: '05-13' },
      { title: '培养管理开放时间策略已进入审核', date: '05-12' },
      { title: '首页口径映射字段已完成校验', date: '05-10' },
      { title: '系统参数备份任务执行成功', date: '05-09' },
    ],
  },
  todoCard: {
    title: '配置待办',
    items: [
      { label: '待发布参数项', count: 4 },
      { label: '待审核模板', count: 3 },
      { label: '待校验同步任务', count: 2 },
      { label: '待清理历史版本', count: 1 },
    ],
  },
}

export const personalCenterMockData = {
  title: '个人中心',
  subtitle: '维护个人资料、岗位信息与日常偏好设置',
  profile: {
    name: '张老师',
    role: '教务秘书',
    department: '研究生教务办公室',
    jobNo: 'SDU2026',
    phone: '13800001234',
    email: 'teacher@sdu.edu.cn',
    lastLogin: '2026-05-13 08:26',
  },
  profileTags: [
    { label: '系统管理员', type: 'primary' },
    { label: '消息提醒已开启', type: 'success' },
    { label: '双因素校验未开启', type: 'info' },
  ],
  statCards: [
    { title: '本月处理事项', number: '86', icon: 'clipboard', iconBg: '#EEF4FF', changeLabel: '覆盖 7 个模块' },
    { title: '待办完成率', number: '93%', icon: 'check-circle', iconBg: '#EEFDF3', changeLabel: '较上月 +4.1%' },
    { title: '发出通知数', number: '24', icon: 'send', iconBg: '#ECFEFF', changeLabel: '其中紧急通知 3 条' },
    { title: '账号安全评分', number: '82分', icon: 'shield', iconBg: '#EEFDF3', changeLabel: '建议开启双因素验证' },
  ],
  quickActions: [
    { label: '偏好设置', desc: '维护默认首页和消息策略' },
    { label: '安全校验', desc: '配置密码与设备校验方式' },
    { label: '操作授权', desc: '查看当前岗位功能授权范围' },
  ],
  operationLogs: [
    { time: '05-13 09:05', module: '培养管理', action: '批量审核培养计划 6 项', status: '成功', statusType: 'success' },
    { time: '05-13 08:48', module: '系统设置', action: '更新首页展示口径配置', status: '成功', statusType: 'success' },
    { time: '05-12 16:20', module: '学位管理', action: '更新答辩通知模板', status: '待生效', statusType: 'warning' },
    { time: '05-12 10:12', module: '系统设置', action: '修改消息模板推送策略', status: '审核中', statusType: 'info' },
  ],
  shortcuts: [
    { label: '系统设置', route: '/system' },
    { label: '修改密码', route: '/change-pwd' },
    { label: '答辩管理', route: '/degree-defense' },
  ],
}

export const changePasswordMockData = {
  title: '修改密码',
  subtitle: '建议定期更新密码，并保持与其他系统账户不同',
  securityTips: [
    { title: '长度建议', desc: '建议密码长度不少于 8 位，并包含数字与字母。' },
    { title: '定期更新', desc: '建议每 90 天更换一次密码，避免长期使用相同口令。' },
    { title: '安全退出', desc: '修改完成后系统会要求重新登录，以确保账号安全。' },
  ],
  passwordLogs: [
    { time: '2026-05-01 10:25', action: '修改登录密码', device: 'Chrome / Windows', status: '成功', statusType: 'success' },
    { time: '2026-04-10 09:14', action: '登录密码校验', device: 'Edge / Windows', status: '成功', statusType: 'success' },
    { time: '2026-03-22 18:06', action: '密码尝试失败', device: 'Chrome / Android', status: '已拦截', statusType: 'warning' },
  ],
}

const graduateManagementMock = {
  sharedOptions,
  home: homeMockData,
  admission: admissionMockData,
  academicStatus: academicStatusMockData,
  training: trainingMockData,
  degree: degreeMockData,
  scholarship: scholarshipMockData,
  employment: employmentMockData,
  academicChange: academicChangeMockData,
  trainingCourse: trainingCourseMockData,
  degreeDefense: degreeDefenseMockData,
  intelligentPrediction: intelligentPredictionMockData,
  systemSettings: systemSettingsMockData,
  personalCenter: personalCenterMockData,
  changePassword: changePasswordMockData,
}

export default graduateManagementMock
