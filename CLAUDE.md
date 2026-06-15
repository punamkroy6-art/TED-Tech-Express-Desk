# TED PROJECT — Vision AI

## Project Overview
This is a static HTML landing page for the **Vision AI** enterprise SaaS product — an intelligent visual intelligence platform targeting corporate clients.

## Files
- `landing-page.html` — Single-file landing page (HTML + CSS, no external dependencies)

## Page Structure
The landing page is organized into the following sections (in order):

1. **Nav** — Sticky top bar with logo, nav links, and "Get Started Free" CTA
2. **Hero** — Full-width dark gradient hero with headline, subtext, two CTAs, and a simulated dashboard screenshot
3. **Trusted By** — Logo bar with enterprise client names
4. **Features** (`#features`) — 6 feature cards (Object Detection, Predictive Analytics, Security, Alerting, Edge/Cloud Deployment, Unified Dashboard)
5. **How It Works** (`#how`) — 4-step process with numbered indicators and connector line
6. **Stats** — Dark banner with 4 key metrics (accuracy, customers, events processed, latency)
7. **Testimonials** — 3 customer quote cards with reviewer info
8. **Pricing** (`#pricing`) — 3-tier plans: Starter ($299/mo), Professional ($899/mo), Enterprise (custom)
9. **CTA Banner** (`#contact`) — Final conversion section with two action buttons
10. **Footer** — Brand blurb, 4-column link grid, copyright

## Design System
- **Style:** Corporate & Trustworthy
- **Primary colors:** Navy (`#0d1f3c`), Blue (`#1e4db7`, `#2563eb`), Accent cyan (`#0ea5e9`)
- **Font:** Segoe UI / system-ui
- **No external CSS frameworks** — all styles are inline via `<style>` in the single file
- **No JavaScript dependencies** — pure HTML/CSS
- **Responsive:** Mobile breakpoint at 768px (nav links hidden, sidebar hidden, step connectors hidden)

## Key CSS Variables
```css
--navy: #0d1f3c
--blue: #1e4db7
--blue-light: #2563eb
--accent: #0ea5e9
--accent-light: #bae6fd
```

## How to Edit
- All content (copy, pricing, feature descriptions) lives directly in `landing-page.html`
- All styles are in the `<style>` block at the top of the file — search by section comment (e.g., `/* ── HERO ── */`)
- To change colors globally, update the CSS variables in `:root`
- To add a new section, insert it between the relevant HTML comment blocks and add a corresponding `<a href="#id">` in the nav

## Deployment
Static file — can be served from any web server, CDN, or opened directly in a browser. No build step required.
