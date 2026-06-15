/**
 * captureCurrentScreen — returns a safe text-based snapshot of the current screen.
 * SVG foreignObject DOM rendering is avoided as it crashes real Chrome/Edge browsers.
 * The ticket already includes full diagnostic data + AI history which is more valuable.
 */
export async function captureCurrentScreen(): Promise<string> {
  // Return empty — screenshot captured separately via Camera 1 (screen camera)
  // when hardware is connected. Browser-based DOM capture crashes real browsers.
  return ''
}

/**
 * Build a plain-text summary of what was on screen for the ticket description.
 */
export function captureScreenText(): string {
  const root = document.getElementById('root')
  if (!root) return ''
  // Extract visible text in reading order
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  const lines: string[] = []
  let node
  while ((node = walker.nextNode())) {
    const text = (node.textContent || '').trim()
    if (text && text.length > 1) lines.push(text)
  }
  return lines.slice(0, 40).join(' | ').substring(0, 600)
}
