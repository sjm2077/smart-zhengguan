// Deliberately limited Markdown: headings, paragraphs, bold and flat lists.
// No HTML or URL generation. Vue must render all text via interpolation.
type Part = { text: string; bold: boolean }
type Block =
  | { kind: 'heading' | 'paragraph'; parts: Part[] }
  | { kind: 'ordered' | 'unordered'; items: Part[][]; start: number }

function inline(text: string): Part[] {
  const result: Part[] = []
  const pattern = /\*\*([^*\n]+)\*\*|__([^_\n]+)__/g
  let pos = 0
  for (const match of text.matchAll(pattern)) {
    const index = match.index ?? 0
    if (index > pos) result.push({ text: text.slice(pos, index), bold: false })
    result.push({ text: match[1] ?? match[2] ?? '', bold: true })
    pos = index + match[0].length
  }
  if (pos < text.length) result.push({ text: text.slice(pos), bold: false })
  return result
}

export function formatAnswer(text: string): Block[] {
  const blocks: Block[] = []
  let paragraph: string[] = []
  let list: Extract<Block, { items: Part[][] }> | undefined
  function flush() {
    if (paragraph.length) blocks.push({ kind: 'paragraph', parts: inline(paragraph.join('\n')) })
    if (list) blocks.push(list)
    paragraph = []
    list = undefined
  }
  for (const raw of text.replace(/\r\n?/g, '\n').split('\n')) {
    const line = raw.trim()
    if (!line) { flush(); continue }
    const heading = /^#{1,6}\s+(.+)$/.exec(line)
    if (heading) {
      flush()
      blocks.push({ kind: 'heading', parts: inline(heading[1]!.replace(/\s+#+$/, '')) })
      continue
    }
    const ordered = /^(\d{1,4})[.)]\s+(.+)$/.exec(line)
    const unordered = /^[-*+]\s+(.+)$/.exec(line)
    if (ordered || unordered) {
      const kind = ordered ? 'ordered' : 'unordered'
      const start = ordered ? Number(ordered[1]) : 1
      if (!list || list.kind !== kind || (kind === 'ordered' && start !== list.start + list.items.length)) {
        flush()
        list = { kind, items: [], start }
      }
      list.items.push(inline(ordered?.[2] ?? unordered?.[1] ?? ''))
      continue
    }
    if (list) flush()
    paragraph.push(line)
  }
  flush()
  return blocks
}
