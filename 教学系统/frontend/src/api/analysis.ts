import api from "./index";

export interface ScoreDistribution {
  score_range: string;
  count: number;
}

export interface CourseScoreStat {
  course_id: number;
  course_name: string;
  avg_score: number;
  pass_rate: number;
  excellent_rate: number;
}

export interface SemesterTrend {
  semester_id: number;
  semester_name: string;
  avg_score: number;
  pass_rate: number;
}

/** GET /api/analysis/score-distribution/ */
export function getScoreDistribution(params?: {
  semester_id?: number;
  college_id?: number;
  course_id?: number;
}): Promise<ScoreDistribution[]> {
  return api.get("/analysis/score-distribution/", { params }).then((res: any) => res.distribution);
}

/** GET /api/analysis/course-scores/ */
export function getCourseScores(params?: {
  semester_id?: number;
  college_id?: number;
}): Promise<CourseScoreStat[]> {
  return api.get("/analysis/course-scores/", { params }).then((res: any) => res.course_stats);
}

/** GET /api/analysis/semester-trend/ */
export function getSemesterTrend(params?: {
  college_id?: number;
  course_id?: number;
}): Promise<SemesterTrend[]> {
  return api
    .get("/analysis/semester-trend/", { params })
    .then((res: any): SemesterTrend[] => {
      // 后端当前直接返回数组
      if (Array.isArray(res)) {
        return res as SemesterTrend[];
      }

      // 兼容将来使用 { trend: [...] } 的响应格式
      if (res && Array.isArray(res.trend)) {
        return res.trend as SemesterTrend[];
      }

      return [];
    });
}


/** GET /api/analysis/student-ranking/ */
export function getStudentRanking(params?: {
  semester_id?: number;
  college_id?: number;
  limit?: number;
}): Promise<
  Array<{
    student_id: number;
    student_name: string;
    avg_score: number;
    rank: number;
  }>
> {
  return api.get("/analysis/student-ranking/", { params });
}

export interface GradeTypeComparisonItem {
  exam_type: string;
  count: number;
  avg_score: number;
  pass_rate: number;
  excellent_rate: number;
}

export interface GradeTypeComparison {
  semester_id: number | null;
  semester_name: string;
  grade_type_stats: GradeTypeComparisonItem[];
}

/** GET /api/analysis/grade-type-comparison/ */
export function getGradeTypeComparison(params?: {
  semester_id?: number;
}): Promise<GradeTypeComparison> {
  return api.get("/analysis/grade-type-comparison/", {
    params,
  });
}
