/**
 * screenshot.ts — Permanent screen capture using html2canvas
 *
 * html2canvas walks the DOM and paints it onto a real <canvas> element
 * entirely within the browser's 2D rasteriser — no SVG foreignObject,
 * no GPU filter pipeline, no cross-origin issues.
 */
import html2canvas from 'html2canvas'

/**
 * Capture the current visible kiosk screen as a base64 JPEG.
 * Used to attach the error screen to the Freshservice ticket.
 */
export async function captureCurrentScreen(quality = 0.8): Promise<string> {
  try {
    const root = document.getElementById('root')
    if (!root) return ''

    const canvas = await html2canvas(root, {
      backgroundColor: '#070b14',   // match TED dark background
      scale: 0.6,                   // reduce resolution for ticket attachment
      logging: false,
      useCORS: false,
      allowTaint: true,
      imageTimeout: 3000,
      removeContainer: true,
    })

    // Return base64-encoded JPEG (strip the data: prefix)
    return canvas.toDataURL('image/jpeg', quality).split(',')[1] ?? ''
  } catch {
    // Never crash the escalation flow if screenshot fails
    return ''
  }
}

/**
 * Extract visible text from the current screen for ticket context.
 * Used as a fallback description when screenshot isn't available.
 */
export function captureScreenText(): string {
  const root = document.getElementById('root')
  if (!root) return ''

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  const lines: string[] = []
  let node: Node | null

  while ((node = walker.nextNode())) {
    const text = (node.textContent ?? '').trim()
    if (text.length > 2) lines.push(text)
  }

  return lines.slice(0, 40).join(' | ').substring(0, 600)
}
