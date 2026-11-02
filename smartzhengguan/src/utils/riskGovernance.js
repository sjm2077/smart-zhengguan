export function hasStudentName(student) {
  const name = String(student.name || '').trim()
  return Boolean(name && !/^(?:学生\s*\d+|AUTO\d+|\d+)$/i.test(name)
    && name !== String(student.studentId || '').trim())
}

export function isImportedPredictionStudent(student) {
  return student.dataSource === 'measured' && hasStudentName(student)
}

export function buildGovernanceGauges(students) {
  const definitions = [
    { key: 'overdue', title: '任务逾期率', field: 'overdueTasksCount',
      matches: (value) => value > 0, rule: '任务逾期次数 > 0', color: '#F59E0B' },
    { key: 'training', title: '培养节点未完成率', field: 'trainingPlanCompletionRate',
      matches: (value) => value < 100, rule: '培养节点尚未完成', color: '#F59E0B' },
    { key: 'communication', title: '导师沟通不足率', field: 'advisorMeetingCount60d',
      matches: (value) => value < 2, rule: '导师沟通次数 < 2（本页判定规则）', color: '#FB923C' },
    { key: 'risk', title: '高风险学生占比',
      rule: '风险等级为“高风险”', color: '#EF4444' },
  ]
  return definitions.map((definition) => {
    // Missing measurements are excluded from the denominator, never treated as zero.
    const eligible = definition.field
      ? students.filter((student) => {
        const value = student.currentSnapshot?.[definition.field]
        return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
      })
      : students.filter((student) => Boolean(student.riskLevel))
    const count = eligible.filter((student) => definition.field
      ? definition.matches(Number(student.currentSnapshot[definition.field]))
      : student.riskLevel === '高风险').length
    return {
      ...definition,
      value: eligible.length ? Number((count * 100 / eligible.length).toFixed(1)) : 0,
      status: eligible.length ? `${count} / ${eligible.length} 人` : '暂无数据',
      students: eligible.filter((student) => definition.field
        ? definition.matches(Number(student.currentSnapshot[definition.field]))
        : student.riskLevel === '高风险'),
      rule: definition.rule,
    }
  })
}
