import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const source = await readFile(new URL('../src/utils/riskGovernance.js', import.meta.url), 'utf8')
const { buildGovernanceGauges, isImportedPredictionStudent } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
)

test('only imported students with a name enter governance statistics', () => {
  const student = { name: '张三', studentId: '2023010001', dataSource: 'measured' }
  assert.equal(isImportedPredictionStudent(student), true)
  for (const change of [
    { dataSource: 'virtual' }, { name: '学生0139' }, { name: '2023010001' }, { name: '' },
  ]) {
    assert.equal(isImportedPredictionStudent({ ...student, ...change }), false)
  }
})

test('rates count students rather than averaging risk scores', () => {
  const rows = [
    { riskLevel: '高风险', gauges: { risk: 100 }, currentSnapshot: {
      overdueTasksCount: 1, trainingPlanCompletionRate: 72, advisorMeetingCount60d: 1,
    } },
    { riskLevel: '低风险', gauges: { risk: 100 }, currentSnapshot: {
      overdueTasksCount: 0, trainingPlanCompletionRate: 100, advisorMeetingCount60d: 2,
    } },
    { riskLevel: '预警', gauges: { risk: 100 }, currentSnapshot: {
      overdueTasksCount: 0, trainingPlanCompletionRate: 100, advisorMeetingCount60d: 3,
    } },
  ]
  for (const gauge of buildGovernanceGauges(rows)) {
    assert.equal(gauge.value, 33.3)
    assert.equal(gauge.status, '1 / 3 人')
    assert.equal(gauge.students.length, 1)
    assert.equal(gauge.students[0], rows[0])
    assert.equal(gauge.trend, undefined)
  }
})

test('missing values are excluded and an empty scope has no fabricated data', () => {
  const gauges = buildGovernanceGauges([
    { currentSnapshot: { overdueTasksCount: 0 } },
    { currentSnapshot: {} },
  ])
  assert.equal(gauges[0].status, '0 / 1 人')
  assert.equal(gauges[1].status, '暂无数据')
  assert.equal(gauges[3].status, '暂无数据')
  for (const gauge of buildGovernanceGauges([])) {
    assert.equal(gauge.value, 0)
    assert.equal(gauge.status, '暂无数据')
    assert.deepEqual(gauge.students, [])
  }
})
