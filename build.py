#!/usr/bin/env python3
"""Build radarv2 vault HTML into a GitHub Pages site."""

import os
import re
import shutil
import html as html_mod
from pathlib import Path

SRC = Path("/home/berkay/projects/aros-private/vault/radarv2")
DST = Path("/home/berkay/projects/radarv2-docs")

# Known wikilink targets (relative to site root)
WIKILINK_MAP = {
    "00-Index": "00-Index.html",
    "01-System-Overview": "01-System-Overview.html",
    "02-Physics-and-Waveform": "02-Physics-and-Waveform.html",
    "03-Beamforming-and-Scan": "03-Beamforming-and-Scan.html",
    "04-Signal-Processing-Pipeline": "04-Signal-Processing-Pipeline.html",
    "05-Node-Architecture": "05-Node-Architecture.html",
    "06-Message-Catalog": "06-Message-Catalog.html",
    "07-Detection-and-Tracking": "07-Detection-and-Tracking.html",
    "08-Scenarios-and-Targets": "08-Scenarios-and-Targets.html",
    "09-Concepts-Primer": "09-Concepts-Primer.html",
    "10-Radar-Model-Library": "10-Radar-Model-Library.html",
    "11-Multi-Radar-Fusion": "11-Multi-Radar-Fusion.html",
    "12-3D-Scene": "12-3D-Scene.html",
    "13-Reference-Tables": "13-Reference-Tables.html",
    "FUTURE-DEVELOPMENT": "FUTURE-DEVELOPMENT.html",
    "MapProvider": "05-Node-Architecture.html",
    "3-D scene (FD-5)": "12-3D-Scene.html",
    "3-D Lichtblick scene": "12-3D-Scene.html",
}

NAV_TEMPLATE = """\
<body class="markdown-reading-view">
<!-- Site header -->
<header class="site-header">
  <a href="{root}00-Index.html" class="site-title">
    radarv2
    <span class="site-title-badge">AERIS-10</span>
  </a>
  <div class="site-subtitle">aros Radar Documentation</div>
  <div class="site-header-links">
    <a href="https://github.com/brkay54/radarv2-docs" target="_blank">GitHub</a>
    <a href="{root}upstream/README.html">Upstream Theory</a>
  </div>
</header>
<div class="site-shell">
  <!-- Sidebar -->
  <nav class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-project">radarv2 Docs</div>
      <div class="sidebar-version">AERIS-10 · aros example</div>
    </div>
    <ul class="nav-list">
      <li class="nav-section">Getting Started</li>
      <li><a href="{root}09-Concepts-Primer.html">Radar Primer (101)</a></li>
      <li><a href="{root}00-Index.html">Index</a></li>
      <li><a href="{root}01-System-Overview.html">System Overview</a></li>
      <li class="nav-section">Core Docs</li>
      <li><a href="{root}02-Physics-and-Waveform.html">Physics &amp; Waveform</a></li>
      <li><a href="{root}03-Beamforming-and-Scan.html">Beamforming &amp; Scan</a></li>
      <li><a href="{root}04-Signal-Processing-Pipeline.html">Signal Processing</a></li>
      <li><a href="{root}05-Node-Architecture.html">Node Architecture</a></li>
      <li><a href="{root}06-Message-Catalog.html">Message Catalog</a></li>
      <li><a href="{root}07-Detection-and-Tracking.html">Detection &amp; Tracking</a></li>
      <li><a href="{root}08-Scenarios-and-Targets.html">Scenarios &amp; Targets</a></li>
      <li class="nav-section">Advanced</li>
      <li><a href="{root}10-Radar-Model-Library.html">Radar Model Library</a></li>
      <li><a href="{root}11-Multi-Radar-Fusion.html">Multi-Radar Fusion</a></li>
      <li><a href="{root}12-3D-Scene.html">3-D Scene</a></li>
      <li><a href="{root}13-Reference-Tables.html">Reference Tables</a></li>
      <li><a href="{root}FUTURE-DEVELOPMENT.html">Future Development</a></li>
      <li class="nav-section">Upstream Theory</li>
      <li><a href="{root}upstream/README.html">Overview</a></li>
      <li><a href="{root}upstream/00_notation/conventions.html">Notation</a></li>
      <li><a href="{root}upstream/01_physics/01_fmcw_theory.html">FMCW Theory</a></li>
      <li><a href="{root}upstream/01_physics/02_lfm_waveform_model.html">LFM Waveform</a></li>
      <li><a href="{root}upstream/01_physics/03_beamforming_theory.html">Beamforming Theory</a></li>
      <li><a href="{root}upstream/01_physics/04_detection_theory.html">Detection Theory</a></li>
      <li><a href="{root}upstream/01_physics/05_noise_analysis.html">Noise Analysis</a></li>
      <li><a href="{root}upstream/01_physics/06_calibration_theory.html">Calibration</a></li>
      <li><a href="{root}upstream/02_hardware/01_system_overview.html">HW Overview</a></li>
      <li><a href="{root}upstream/04_research/01_cfar_variants.html">CFAR Variants</a></li>
    </ul>
    <div class="sidebar-footer">
      <a href="https://github.com/brkay54/radarv2-docs" target="_blank">GitHub ↗</a>
    </div>
  </nav>
  <!-- Main -->
  <div class="main-content">
"""

BODY_CLOSE = """\
  </div><!-- main-content -->
</div><!-- site-shell -->
<script>
mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'loose',
  fontFamily: 'Inter, system-ui, sans-serif',
  fontSize: 14,
  flowchart: { useMaxWidth: false, htmlLabels: true, curve: 'basis' },
  sequence:  { useMaxWidth: false },
  er:        { useMaxWidth: false },
  gantt:     { useMaxWidth: false },
});

async function initMermaid() {
  var elements = document.querySelectorAll('.mermaid');
  if (!elements.length) return;
  try { await mermaid.run({ querySelector: '.mermaid' }); } catch(e) { console.error('mermaid', e); }
  elements.forEach(function(container) {
    var svg = container.querySelector('svg');
    if (!svg) return;
    svg.removeAttribute('width');
    svg.removeAttribute('height');
    svg.style.cssText = 'width:100%;height:100%;max-width:none;display:block;';
    if (!svg.getAttribute('viewBox')) {
      try { var b=svg.getBBox(); svg.setAttribute('viewBox',b.x+' '+b.y+' '+b.width+' '+b.height); } catch(_){}
    }
    try {
      var pz = svgPanZoom(svg, {
        zoomEnabled: true, controlIconsEnabled: true,
        fit: true, center: true,
        minZoom: 0.2, maxZoom: 20,
        zoomScaleSensitivity: 0.25,
        mouseWheelZoomEnabled: true,
        dblClickZoomEnabled: false,
      });
      svg.addEventListener('dblclick', function() { pz.resetZoom(); pz.center(); });
      var hint = document.createElement('div');
      hint.className = 'mermaid-hint';
      hint.textContent = 'Scroll to zoom · drag to pan · dbl-click to reset';
      container.appendChild(hint);
    } catch(e) { console.error('svgPanZoom', e); }
  });
}

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', initMermaid); }
else { initMermaid(); }
</script>
</body>
"""

HEAD_INJECT = """\
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<!-- Mermaid -->
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<!-- svg-pan-zoom for interactive mermaid diagrams -->
<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
<!-- MathJax -->
<script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}},options:{{skipHtmlTags:['script','noscript','style','textarea','pre']}}}};</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" async></script>
<!-- Site CSS -->
<link rel="stylesheet" href="{css_path}">
</head>"""


def depth_from_root(rel_path: Path) -> int:
    """Number of directory levels below site root."""
    return len(rel_path.parent.parts)


def root_prefix(depth: int) -> str:
    return "../" * depth


def css_path(depth: int) -> str:
    return root_prefix(depth) + "site.css"


def convert_mermaid(content: str) -> str:
    def replace(m):
        raw = html_mod.unescape(m.group(1))
        return f'<div class="mermaid">{raw}</div>'
    return re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        replace,
        content,
        flags=re.DOTALL,
    )


def convert_wikilinks(content: str, depth: int) -> str:
    root = root_prefix(depth)

    def replace(m):
        text = m.group(1)
        if text in WIKILINK_MAP:
            href = root + WIKILINK_MAP[text]
            return f'<a href="{href}" class="internal-link">{text}</a>'
        return f'<span class="wikilink-unresolved">{text}</span>'

    return re.sub(r'<span class="wikilink">([^<]+)</span>', replace, content)


def add_nav(content: str, depth: int) -> str:
    root = root_prefix(depth)
    nav = NAV_TEMPLATE.format(root=root)
    # Replace <body ...> opening tag
    content = re.sub(r'<body[^>]*>', nav, content, count=1)
    # Replace </body>
    content = content.replace("</body>", BODY_CLOSE, 1)
    return content


def inject_head(content: str, depth: int) -> str:
    inject = HEAD_INJECT.format(css_path=css_path(depth))
    content = content.replace("</head>", inject, 1)
    return content


def remove_inline_style(content: str) -> str:
    # Remove the inline style from .markdown-preview-section div
    content = re.sub(
        r'(<div class="markdown-preview-section") style="[^"]*"',
        r'\1',
        content,
    )
    return content


def process_html(src_file: Path, rel: Path):
    depth = depth_from_root(rel)
    content = src_file.read_text(encoding="utf-8")

    content = inject_head(content, depth)
    content = convert_mermaid(content)
    content = convert_wikilinks(content, depth)
    content = add_nav(content, depth)
    content = remove_inline_style(content)

    dst_file = DST / rel
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    dst_file.write_text(content, encoding="utf-8")
    print(f"  processed: {rel}")


def copy_binary(src_file: Path, rel: Path):
    dst_file = DST / rel
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dst_file)
    print(f"  copied:    {rel}")


def write_site_css():
    css = """\
/* radarv2-docs — Slate + Indigo theme (Layout 001-A, Palette 002-B) */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --sidebar-width: 260px;
  --header-height: 52px;

  --color-bg:            #ffffff;
  --color-surface:       #f8fafc;
  --color-surface-alt:   #f1f5f9;
  --color-border:        #cbd5e1;
  --color-border-light:  #e2e8f0;

  --color-text:          #0f172a;
  --color-text-muted:    #475569;
  --color-text-subtle:   #94a3b8;

  --color-primary:       #4f46e5;
  --color-primary-dark:  #3730a3;
  --color-primary-light: #eef2ff;
  --color-primary-bg:    #f5f3ff;

  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

*, *::before, *::after { box-sizing: border-box; }

body {
  font-family: var(--font-sans);
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.65;
  font-size: 15px;
  margin: 0;
  padding-top: var(--header-height);
}

/* ── Top header ── */
.site-header {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: var(--header-height);
  background: #1e1b4b;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 16px;
  z-index: 200;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.site-title {
  font-family: var(--font-sans);
  font-size: 16px;
  font-weight: 800;
  color: #fff;
  text-decoration: none;
  letter-spacing: -.02em;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.site-title:hover { color: #e0e7ff; text-decoration: none; }

.site-title-badge {
  font-size: 10px;
  font-weight: 600;
  background: rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.75);
  padding: 2px 7px;
  border-radius: 20px;
  letter-spacing: .05em;
  text-transform: uppercase;
}

.site-subtitle {
  font-size: 11px;
  color: rgba(255,255,255,0.38);
  font-family: var(--font-sans);
}

.site-header-links {
  margin-left: auto;
  display: flex;
  gap: 2px;
}

.site-header-links a {
  color: rgba(255,255,255,0.65);
  text-decoration: none;
  font-size: 13px;
  font-family: var(--font-sans);
  padding: 5px 10px;
  border-radius: 5px;
  transition: all .12s;
}

.site-header-links a:hover {
  background: rgba(255,255,255,0.1);
  color: #fff;
  text-decoration: none;
}

/* ── Shell ── */
.site-shell { display: flex; min-height: calc(100vh - var(--header-height)); }

/* ── Sidebar ── */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  position: fixed;
  top: var(--header-height);
  bottom: 0;
  left: 0;
  overflow-y: auto;
  padding: 14px 0 40px;
  z-index: 100;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}

.sidebar-header {
  padding: 6px 16px 12px;
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: 6px;
}

.sidebar-project {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text);
  font-family: var(--font-sans);
}

.sidebar-version {
  font-size: 11px;
  color: var(--color-text-subtle);
  margin-top: 2px;
  font-family: var(--font-sans);
}

.nav-section {
  padding: 10px 16px 3px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--color-text-subtle);
  font-family: var(--font-sans);
  pointer-events: none;
}

.nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.nav-list li a {
  display: block;
  padding: 5px 16px;
  font-size: 13px;
  font-family: var(--font-sans);
  color: var(--color-text-muted);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: all .1s;
  line-height: 1.4;
}

.nav-list li a:hover {
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-left-color: var(--color-primary);
}

.nav-list li a.nav-active {
  color: var(--color-primary);
  background: var(--color-primary-bg);
  border-left-color: var(--color-primary);
  font-weight: 600;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--color-border-light);
  margin-top: 14px;
  font-size: 12px;
  font-family: var(--font-sans);
}

.sidebar-footer a {
  color: var(--color-text-subtle);
  text-decoration: none;
}

.sidebar-footer a:hover { color: var(--color-primary); text-decoration: none; }

/* ── Main content ── */
.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  min-width: 0;
}

.markdown-preview-section {
  max-width: 860px;
  margin: 0 auto;
  padding: 40px 48px 80px;
  font-family: var(--font-sans);
}

/* ── Typography ── */
h1 { font-size: 28px; font-weight: 800; line-height: 1.25; color: var(--color-text); margin: 0 0 8px; letter-spacing: -.02em; }
h2 { font-size: 20px; font-weight: 700; color: var(--color-text); margin: 36px 0 14px; padding-bottom: 8px; border-bottom: 1px solid var(--color-border-light); }
h3 { font-size: 16px; font-weight: 600; color: var(--color-text); margin: 24px 0 10px; }
h4 { font-size: 14px; font-weight: 600; color: var(--color-text-muted); margin: 20px 0 8px; text-transform: uppercase; letter-spacing: .05em; }

p { color: var(--color-text-muted); margin: 0 0 14px; line-height: 1.7; }

a { color: var(--color-primary); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Code ── */
code {
  font-family: var(--font-mono);
  font-size: .85em;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border-light);
  padding: 2px 5px;
  border-radius: 4px;
  color: #7c3aed;
}

pre {
  background: #0f172a;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 18px 20px;
  overflow-x: auto;
  margin: 16px 0;
}

pre code {
  background: none;
  border: none;
  padding: 0;
  color: #e2e8f0;
  font-size: 13px;
}

/* ── Mermaid — interactive pan/zoom ── */
.mermaid {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin: 20px 0;
  overflow: hidden;
  min-height: 380px;
  height: 380px;
  position: relative;
  cursor: grab;
  user-select: none;
}
.mermaid:active { cursor: grabbing; }
.mermaid svg {
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  display: block;
}
/* svg-pan-zoom control icons */
.mermaid .svg-pan-zoom-control { cursor: pointer; }
.mermaid-hint {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  color: var(--color-text-subtle);
  background: rgba(255,255,255,0.9);
  padding: 3px 10px;
  border-radius: 20px;
  pointer-events: none;
  white-space: nowrap;
  border: 1px solid var(--color-border-light);
  font-family: var(--font-sans);
  backdrop-filter: blur(4px);
}

/* ── Tables ── */
.md-table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
  font-size: 13px;
  font-family: var(--font-sans);
}

.md-table th {
  background: var(--color-surface);
  padding: 8px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--color-text);
  border: 1px solid var(--color-border);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .04em;
}

.md-table td {
  padding: 8px 14px;
  border: 1px solid var(--color-border-light);
  color: var(--color-text-muted);
  vertical-align: top;
}

.md-table tr:hover td { background: var(--color-surface); }

/* ── Callouts ── */
.callout {
  border-radius: 6px;
  padding: 12px 16px;
  margin: 16px 0;
  border-left: 3px solid var(--color-primary);
  background: var(--color-primary-light);
  font-size: 14px;
}

.callout-title {
  font-weight: 700;
  margin-bottom: 4px;
  color: var(--color-primary-dark);
  font-size: 13px;
  font-family: var(--font-sans);
}

.callout-content { color: var(--color-text-muted); }
.callout-content p { color: var(--color-text-muted); margin-bottom: 4px; }

.callout[data-callout="warning"]  { border-color: #d97706; background: #fffbeb; }
.callout[data-callout="warning"] .callout-title  { color: #92400e; }
.callout[data-callout="danger"],
.callout[data-callout="error"]    { border-color: #dc2626; background: #fef2f2; }
.callout[data-callout="danger"] .callout-title,
.callout[data-callout="error"] .callout-title   { color: #991b1b; }
.callout[data-callout="info"]     { border-color: #0ea5e9; background: #f0f9ff; }
.callout[data-callout="info"] .callout-title    { color: #0369a1; }
.callout[data-callout="note"]     { border-color: #16a34a; background: #f0fdf4; }
.callout[data-callout="note"] .callout-title    { color: #15803d; }
.callout[data-callout="abstract"] { border-color: #0ea5e9; background: #f0f9ff; }
.callout[data-callout="abstract"] .callout-title{ color: #0369a1; }
.callout[data-callout="tip"]      { border-color: #16a34a; background: #f0fdf4; }
.callout[data-callout="tip"] .callout-title     { color: #15803d; }

/* ── Internal links ── */
.internal-link {
  color: var(--color-primary);
  text-decoration: none;
  border-bottom: 1px solid #c7d2fe;
}
.internal-link:hover {
  color: var(--color-primary-dark);
  border-bottom-color: var(--color-primary);
  text-decoration: none;
}
.wikilink-unresolved { color: var(--color-text-subtle); font-style: italic; }

/* ── Heading anchors ── */
.ha { opacity: 0; margin-left: 6px; font-size: .75em; color: var(--color-text-subtle); text-decoration: none; }
h1:hover .ha, h2:hover .ha, h3:hover .ha, h4:hover .ha { opacity: 1; }

/* ── Blockquote / hr / lists ── */
blockquote { border-left: 3px solid var(--color-border); margin: 16px 0; padding: 4px 16px; color: var(--color-text-muted); font-style: italic; }
hr { border: none; border-top: 1px solid var(--color-border-light); margin: 28px 0; }
ul, ol { padding-left: 24px; margin-bottom: 14px; }
li { color: var(--color-text-muted); margin-bottom: 4px; }
li code { font-size: .83em; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .main-content { margin-left: 0; }
  .markdown-preview-section { padding: 24px 20px 60px; }
  .site-subtitle { display: none; }
}
"""
    (DST / "site.css").write_text(css, encoding="utf-8")
    print("  wrote: site.css")


def write_index():
    html = ('<!DOCTYPE html>\n<html><head><meta charset="UTF-8">'
            '<meta http-equiv="refresh" content="0;url=00-Index.html">'
            '<title>radarv2 docs</title></head>'
            '<body><a href="00-Index.html">Go to index</a></body></html>\n')
    (DST / "index.html").write_text(html, encoding="utf-8")
    print("  wrote: index.html")


def main():
    print("Building radarv2-docs site...")
    write_site_css()
    write_index()

    for src_file in sorted(SRC.rglob("*")):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(SRC)
        if src_file.suffix == ".html":
            process_html(src_file, rel)
        elif src_file.suffix in (".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico"):
            copy_binary(src_file, rel)
        # skip .md and other files

    print("Done.")


if __name__ == "__main__":
    main()
