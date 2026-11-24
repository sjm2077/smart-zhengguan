/**
 * 首页科研趋势演示数据。
 *
 * 本项目未连接独立科研系统，因此这里使用前端本地演示数据，
 * 不会发起网络请求，也不会影响教学系统后端接口。
 * 页面标题会明确标注“演示数据”，避免将模拟数据误认为真实统计。
 */
export interface ResearchTrendResponse {
  years: number[];
  values: number[];
}

const DEMO_RESEARCH_TRENDS: Record<string, ResearchTrendResponse> = {
  projects: {
    years: [2021, 2022, 2023, 2024, 2025, 2026],
    values: [8, 11, 13, 16, 19, 22],
  },
  achievements: {
    years: [2021, 2022, 2023, 2024, 2025, 2026],
    values: [14, 18, 21, 27, 31, 36],
  },
};


function getDemoTrend(
  key: "projects" | "achievements",
  requestedYears: number[],
): Promise<ResearchTrendResponse> {
  const source = DEMO_RESEARCH_TRENDS[key];

  // 明确处理可能不存在的数据，满足 TypeScript 严格类型检查。
  if (!source) {
    return Promise.resolve({
      years: [],
      values: [],
    });
  }

  const yearSet = new Set(requestedYears);

  const selected = source.years
    .map((year, index) => ({
      year,
      value: source.values[index] ?? 0,
    }))
    .filter(item => yearSet.has(item.year));

  return Promise.resolve({
    years: selected.map(item => item.year),
    values: selected.map(item => item.value),
  });
}


/** 首页科研项目趋势：本地演示数据，不请求独立科研服务。 */
export function getResearchProjectTrend(years: number[]): Promise<ResearchTrendResponse> {
  return getDemoTrend("projects", years);
}

/** 首页科研成果趋势：本地演示数据，不请求独立科研服务。 */
export function getResearchAchievementTrend(years: number[]): Promise<ResearchTrendResponse> {
  return getDemoTrend("achievements", years);
}
