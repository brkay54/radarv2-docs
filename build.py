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
<div class="site-shell">
  <nav class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <a href="{root}00-Index.html" class="site-title">radarv2 / AERIS-10</a>
      <div class="site-subtitle">aros Radar Documentation</div>
    </div>
    <ul class="nav-list">
      <li class="nav-section">Core Docs</li>
      <li><a href="{root}09-Concepts-Primer.html">Radar Primer</a></li>
      <li><a href="{root}00-Index.html">Index</a></li>
      <li><a href="{root}01-System-Overview.html">System Overview</a></li>
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
      <li><a href="{root}upstream/README.html">Upstream README</a></li>
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
      <a href="https://github.com/brkay54/radarv2-docs" target="_blank">GitHub</a>
    </div>
  </nav>
  <div class="main-content">
"""

BODY_CLOSE = """\
  </div><!-- main-content -->
</div><!-- site-shell -->
<script>
mermaid.initialize({ startOnLoad: true, theme: 'dark', securityLevel: 'loose' });
</script>
</body>
"""

HEAD_INJECT = """\
<!-- Mermaid -->
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
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
/* Site shell layout */
.site-shell {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  min-width: 240px;
  background: #181825;
  border-right: 1px solid #313244;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  overflow-y: auto;
  z-index: 100;
}

.sidebar-header {
  padding: 20px 16px 12px;
  border-bottom: 1px solid #313244;
}

.site-title {
  font-size: 15px;
  font-weight: 700;
  color: #7C3AED;
  text-decoration: none;
  display: block;
  margin-bottom: 4px;
}

.site-title:hover { color: #8B5CF6; }

.site-subtitle {
  font-size: 11px;
  color: #8E8EA0;
}

.nav-list {
  list-style: none;
  margin: 0;
  padding: 8px 0;
  flex: 1;
}

.nav-list li a {
  display: block;
  padding: 5px 16px;
  color: #DCDDDE;
  text-decoration: none;
  font-size: 13px;
  transition: background 0.1s;
}

.nav-list li a:hover {
  background: #313244;
  color: #fff;
}

.nav-section {
  padding: 10px 16px 4px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #8E8EA0;
  pointer-events: none;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #313244;
  font-size: 12px;
}

.sidebar-footer a {
  color: #8E8EA0;
  text-decoration: none;
}

.sidebar-footer a:hover { color: #DCDDDE; }

.main-content {
  margin-left: 240px;
  flex: 1;
  min-width: 0;
}

.markdown-preview-section {
  max-width: 860px;
  margin: 0 auto;
  padding: 32px 40px 80px;
}

/* Internal links */
.internal-link { color: #7C3AED; }
.internal-link:hover { color: #8B5CF6; }
.wikilink-unresolved { color: #8E8EA0; font-style: italic; }

/* Mermaid diagrams */
.mermaid {
  background: #181825;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  overflow-x: auto;
}

/* Tables */
.md-table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
  font-size: 14px;
}
.md-table th, .md-table td {
  border: 1px solid #313244;
  padding: 8px 12px;
  text-align: left;
}
.md-table th { background: #181825; }
.md-table tr:hover td { background: #232332; }

/* Callouts */
.callout {
  border-radius: 6px;
  padding: 12px 16px;
  margin: 16px 0;
  border-left: 4px solid #7C3AED;
  background: #1a1a2e;
}
.callout-title {
  font-weight: 700;
  margin-bottom: 6px;
  color: #8B5CF6;
}
.callout[data-callout="warning"] { border-color: #F59E0B; }
.callout[data-callout="warning"] .callout-title { color: #F59E0B; }
.callout[data-callout="danger"], .callout[data-callout="error"] { border-color: #E5534B; }
.callout[data-callout="danger"] .callout-title,
.callout[data-callout="error"] .callout-title { color: #E5534B; }
.callout[data-callout="info"] { border-color: #007ACC; }
.callout[data-callout="info"] .callout-title { color: #007ACC; }
.callout[data-callout="note"] { border-color: #2DA44E; }
.callout[data-callout="note"] .callout-title { color: #2DA44E; }
.callout[data-callout="abstract"] { border-color: #0BC5EA; }
.callout[data-callout="abstract"] .callout-title { color: #0BC5EA; }
.callout[data-callout="tip"] { border-color: #2DA44E; }
.callout[data-callout="tip"] .callout-title { color: #2DA44E; }

/* Responsive */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .main-content { margin-left: 0; }
}

/* Heading anchors */
.ha { opacity: 0; margin-left: 6px; font-size: 0.8em; color: #8E8EA0; text-decoration: none; }
h1:hover .ha, h2:hover .ha, h3:hover .ha, h4:hover .ha { opacity: 1; }

/* Code blocks */
pre {
  background: #12121e;
  border: 1px solid #313244;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-size: 13px;
}
code { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
p code, li code { background: #2a2a3e; padding: 2px 5px; border-radius: 3px; font-size: 0.9em; }
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
