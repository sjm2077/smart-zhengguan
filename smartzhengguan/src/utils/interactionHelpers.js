import { findBestRoute } from './searchEngine'

function sanitizeCell(value) {
  const text = String(value ?? '')
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

export function findRouteByKeyword(keyword) {
  const matched = findBestRoute(keyword)
  return matched?.path || null
}

export function findRouteByLabel(label) {
  return findRouteByKeyword(label)
}

export function downloadCsv(filename, columns, rows) {
  const header = columns.map((column) => sanitizeCell(column.label)).join(',')
  const body = rows.map((row) =>
    columns.map((column) => sanitizeCell(row[column.key])).join(','),
  )
  const csv = ['\uFEFF' + header, ...body].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
