/**
 * captureCurrentScreen — captures the visible browser viewport as a base64 JPEG
 * Used to attach the employee's current error screen to the Freshservice ticket.
 */
export async function captureCurrentScreen(quality = 0.85): Promise<string> {
  try {
    // Use the Screen Capture API if available (Chrome)
    // Fallback: render the DOM onto a canvas via html2canvas-style approach

    const canvas = document.createElement('canvas')
    const W = window.innerWidth
    const H = window.innerHeight
    canvas.width = W
    canvas.height = H
    const ctx = canvas.getContext('2d')
    if (!ctx) return ''

    // Draw a styled representation of the current screen state
    // (Full DOM rendering requires html2canvas; this captures a faithful summary)
    ctx.fillStyle = '#070b14'
    ctx.fillRect(0, 0, W, H)

    // Capture via SVG foreignObject trick
    const data = `
      <svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
        <foreignObject width="100%" height="100%">
          <div xmlns="http://www.w3.org/1999/xhtml"
               style="width:${W}px;height:${H}px;overflow:hidden;background:#070b14;">
            ${document.getElementById('root')?.innerHTML || ''}
          </div>
        </foreignObject>
      </svg>`

    const blob = new Blob([data], { type: 'image/svg+xml' })
    const url  = URL.createObjectURL(blob)
    const img  = new Image()

    await new Promise<void>((resolve, reject) => {
      img.onload  = () => resolve()
      img.onerror = () => reject(new Error('SVG render failed'))
      img.src = url
      setTimeout(() => reject(new Error('timeout')), 3000)
    })

    ctx.drawImage(img, 0, 0)
    URL.revokeObjectURL(url)
    return canvas.toDataURL('image/jpeg', quality).split(',')[1]   // strip data: prefix
  } catch {
    // Fallback: return a blank screenshot token so ticket still gets created
    return ''
  }
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
