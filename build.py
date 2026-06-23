#!/usr/bin/env python3
"""Build radarv2 vault HTML into a GitHub Pages site."""

import argparse
import html as html_mod
import json
import re
import shutil
from pathlib import Path

# Defaults — overridden by --src / --dst CLI args
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
      <div class="sidebar-search">
        <input id="site-search" type="search" placeholder="Search docs…" autocomplete="off" spellcheck="false">
        <div id="search-results" class="search-results"></div>
      </div>
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
</body>
"""

HEAD_INJECT = """\
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<!-- MathJax -->
<script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}},options:{{skipHtmlTags:['script','noscript','style','textarea','pre']}}}};</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" async></script>
<!-- Site -->
<link rel="stylesheet" href="{css_path}">
<script src="{js_path}" defer></script>
</head>"""


def depth_from_root(rel_path: Path) -> int:
    return len(rel_path.parent.parts)


def root_prefix(depth: int) -> str:
    return "../" * depth


def css_path(depth: int) -> str:
    return root_prefix(depth) + "site.css"


def js_path(depth: int) -> str:
    return root_prefix(depth) + "site.js"


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
    content = re.sub(r'<body[^>]*>', nav, content, count=1)
    content = content.replace("</body>", BODY_CLOSE, 1)
    return content


def inject_head(content: str, depth: int) -> str:
    inject = HEAD_INJECT.format(css_path=css_path(depth), js_path=js_path(depth))
    content = content.replace("</head>", inject, 1)
    return content


def remove_inline_style(content: str) -> str:
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


def write_site_js():
    src = Path(__file__).parent / "site.js"
    dst = DST / "site.js"
    if src.resolve() == dst.resolve():
        print("  skipped: site.js (already in place)")
        return
    content = _read_asset("site.js")
    dst.write_text(content, encoding="utf-8")
    print("  wrote: site.js")


def _write_site_js_inline():
    js = r"""// site.js — radarv2-docs interactive layer

// ── -1. DOM fixup: display math · blockquotes · stray elements ──────────
(function() {
  function fixDisplayMath(container) {
    var changed = true;
    while (changed) {
      changed = false;
      var children = Array.from(container.children);
      for (var i = 0; i < children.length; i++) {
        var el = children[i];
        if (el.tagName !== 'P') continue;
        if (el.textContent.trim() !== '$$') continue;
        var lines = [];
        var j = i + 1;
        while (j < children.length && children[j].tagName === 'P') {
          if (children[j].textContent.trim() === '$$') break;
          lines.push(children[j].textContent);
          j++;
        }
        if (j < children.length && children[j].tagName === 'P' &&
            children[j].textContent.trim() === '$$' && lines.length > 0) {
          var div = document.createElement('div');
          div.className = 'math-block';
          div.textContent = '$$' + lines.join('\n') + '$$';
          container.insertBefore(div, el);
          for (var k = i; k <= j; k++) {
            if (children[k].parentNode) children[k].parentNode.removeChild(children[k]);
          }
          changed = true;
          break;
        }
      }
    }
  }

  function fixStrayElements(container) {
    Array.from(container.children).forEach(function(el) {
      if (el.tagName === 'P') {
        var t = el.textContent.trim();
        if (t === '>' || t === '') el.parentNode.removeChild(el);
      }
    });
  }

  function parseMarkdownTable(lines) {
    try {
      var sepIdx = -1;
      for (var i = 0; i < lines.length; i++) {
        if (/^\|[\s|:-]+\|?\s*$/.test(lines[i])) { sepIdx = i; break; }
      }
      if (sepIdx < 1) return null;

      var splitRow = function(line) {
        return line.replace(/^\||\|$/g, '').split('|').map(function(s) { return s.trim(); });
      };

      var table = document.createElement('table');
      table.className = 'md-table';

      var thead = document.createElement('thead');
      var hrow = document.createElement('tr');
      splitRow(lines[0]).forEach(function(h) {
        var th = document.createElement('th');
        th.textContent = h;
        hrow.appendChild(th);
      });
      thead.appendChild(hrow);
      table.appendChild(thead);

      var tbody = document.createElement('tbody');
      for (var i = sepIdx + 1; i < lines.length; i++) {
        if (!lines[i].startsWith('|')) continue;
        var cells = splitRow(lines[i]);
        var row = document.createElement('tr');
        cells.forEach(function(c) {
          var td = document.createElement('td');
          td.textContent = c;
          row.appendChild(td);
        });
        tbody.appendChild(row);
      }
      table.appendChild(tbody);
      return table;
    } catch(e) { return null; }
  }

  function fixBlockquotes(container) {
    var changed = true;
    while (changed) {
      changed = false;
      var kids = Array.from(container.children);
      for (var i = 0; i < kids.length - 1; i++) {
        if (kids[i].tagName === 'BLOCKQUOTE' && kids[i + 1].tagName === 'BLOCKQUOTE') {
          kids[i].appendChild(document.createElement('br'));
          while (kids[i + 1].firstChild) kids[i].appendChild(kids[i + 1].firstChild);
          kids[i + 1].parentNode.removeChild(kids[i + 1]);
          changed = true;
          break;
        }
      }
    }

    Array.from(container.children).forEach(function(el) {
      if (el.tagName !== 'BLOCKQUOTE') return;
      var text = (el.innerText || el.textContent).trim();
      var lines = text.split('\n').map(function(l) { return l.trim(); }).filter(Boolean);

      var tableStart = -1;
      for (var ti = 0; ti < lines.length; ti++) {
        if (lines[ti].startsWith('|')) { tableStart = ti; break; }
      }
      if (tableStart >= 0) {
        var tbl = parseMarkdownTable(lines.slice(tableStart));
        if (tbl) {
          if (tableStart > 0) {
            var hdr = document.createElement('blockquote');
            hdr.textContent = lines.slice(0, tableStart).join(' ');
            el.parentNode.insertBefore(hdr, el);
          }
          el.parentNode.insertBefore(tbl, el);
          el.parentNode.removeChild(el);
          return;
        }
      }

      var html = el.innerHTML;
      html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      el.innerHTML = html;
    });
  }

  function fixDOM() {
    var container = document.querySelector('.markdown-preview-section');
    if (!container) return;
    fixStrayElements(container);
    fixDisplayMath(container);
    fixBlockquotes(container);
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixDOM);
  } else {
    fixDOM();
  }
})();

// ── 0. Mermaid + svgPanZoom ──────────────────────────────────────────

// ── 0. Mermaid + svgPanZoom ──────────────────────────────────────────
(function() {
  function loadScript(src, cb) {
    var s = document.createElement('script');
    s.src = src;
    s.onload = cb;
    document.head.appendChild(s);
  }

  function initMermaid() {
    if (!document.querySelector('.mermaid')) return;
    loadScript('https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js', function() {
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
      mermaid.run({ querySelector: '.mermaid' }).then(function() {
        document.querySelectorAll('.mermaid').forEach(function(container) {
          var svg = container.querySelector('svg');
          if (!svg) return;
          svg.removeAttribute('width');
          svg.removeAttribute('height');
          svg.style.cssText = 'width:100%;height:100%;max-width:none;display:block;';
          if (!svg.getAttribute('viewBox')) {
            try { var b = svg.getBBox(); svg.setAttribute('viewBox', b.x+' '+b.y+' '+b.width+' '+b.height); } catch(_) {}
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
          } catch(e) {}
        });
      }).catch(function(e) { console.error('mermaid', e); });
    });
  }

  loadScript('https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js', initMermaid);
})();

// ── 1. Active nav highlighting ────────────────────────────────────────
(function() {
  var file = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-list li a').forEach(function(a) {
    var hfile = (a.getAttribute('href') || '').split('/').pop();
    if (hfile && hfile === file) {
      a.classList.add('nav-active');
      setTimeout(function() { a.scrollIntoView({ block: 'nearest' }); }, 100);
    }
  });
})();

// ── 2. Right-side TOC with scroll spy ────────────────────────────────
(function() {
  var section = document.querySelector('.markdown-preview-section');
  if (!section) return;
  var headings = Array.from(section.querySelectorAll('h2, h3'));
  if (headings.length < 2) return;

  var toc = document.createElement('aside');
  toc.className = 'page-toc';
  var tocTitle = document.createElement('div');
  tocTitle.className = 'page-toc-title';
  tocTitle.textContent = 'On this page';
  toc.appendChild(tocTitle);

  var links = [];
  headings.forEach(function(h) {
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent.replace(/¶$/, '').trim();
    a.className = 'toc-link' + (h.tagName === 'H3' ? ' toc-h3' : '');
    toc.appendChild(a);
    links.push({ el: h, link: a });
  });

  var mainContent = document.querySelector('.main-content');
  if (mainContent) {
    mainContent.appendChild(toc);
    document.documentElement.classList.add('has-toc');
  }

  var activeLink = null;
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(e) {
      if (e.isIntersecting) {
        var item = links.find(function(l) { return l.el === e.target; });
        if (item) {
          if (activeLink) activeLink.classList.remove('toc-active');
          activeLink = item.link;
          activeLink.classList.add('toc-active');
        }
      }
    });
  }, { rootMargin: '-60px 0px -70% 0px', threshold: 0 });

  headings.forEach(function(h) { observer.observe(h); });
})();

// ── 3. Prev / Next navigation + keyboard shortcuts ────────────────────
(function() {
  var PAGES = [
    '09-Concepts-Primer.html',
    '00-Index.html',
    '01-System-Overview.html',
    '02-Physics-and-Waveform.html',
    '03-Beamforming-and-Scan.html',
    '04-Signal-Processing-Pipeline.html',
    '05-Node-Architecture.html',
    '06-Message-Catalog.html',
    '07-Detection-and-Tracking.html',
    '08-Scenarios-and-Targets.html',
    '10-Radar-Model-Library.html',
    '11-Multi-Radar-Fusion.html',
    '12-3D-Scene.html',
    '13-Reference-Tables.html',
    'FUTURE-DEVELOPMENT.html',
  ];
  var TITLES = {
    '09-Concepts-Primer.html':           'Radar Primer',
    '00-Index.html':                      'Index',
    '01-System-Overview.html':            'System Overview',
    '02-Physics-and-Waveform.html':       'Physics & Waveform',
    '03-Beamforming-and-Scan.html':       'Beamforming & Scan',
    '04-Signal-Processing-Pipeline.html': 'Signal Processing',
    '05-Node-Architecture.html':          'Node Architecture',
    '06-Message-Catalog.html':            'Message Catalog',
    '07-Detection-and-Tracking.html':     'Detection & Tracking',
    '08-Scenarios-and-Targets.html':      'Scenarios & Targets',
    '10-Radar-Model-Library.html':        'Radar Model Library',
    '11-Multi-Radar-Fusion.html':         'Multi-Radar Fusion',
    '12-3D-Scene.html':                   '3-D Scene',
    '13-Reference-Tables.html':           'Reference Tables',
    'FUTURE-DEVELOPMENT.html':            'Future Development',
  };

  var file = window.location.pathname.split('/').pop() || '';
  var idx = PAGES.indexOf(file);
  if (idx === -1) return;

  var prev = idx > 0 ? PAGES[idx - 1] : null;
  var next = idx < PAGES.length - 1 ? PAGES[idx + 1] : null;

  // Determine root prefix from sidebar link hrefs
  var root = '';
  var navA = document.querySelector('.nav-list li a');
  if (navA) {
    var rel = navA.getAttribute('href') || '';
    var ups = (rel.match(/\.\.\//g) || []).length;
    for (var i = 0; i < ups; i++) root += '../';
  }

  var section = document.querySelector('.markdown-preview-section');
  if (!section) return;

  var pager = document.createElement('nav');
  pager.className = 'doc-pager';

  if (prev) {
    var pa = document.createElement('a');
    pa.href = root + prev;
    pa.className = 'pager-prev';
    pa.innerHTML = '<span class="pager-label">← Previous</span><span class="pager-title">' + TITLES[prev] + '</span>';
    pager.appendChild(pa);
  } else {
    pager.appendChild(document.createElement('span'));
  }

  if (next) {
    var na = document.createElement('a');
    na.href = root + next;
    na.className = 'pager-next';
    na.innerHTML = '<span class="pager-label">Next →</span><span class="pager-title">' + TITLES[next] + '</span>';
    pager.appendChild(na);
  }

  section.appendChild(pager);

  document.addEventListener('keydown', function(e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.altKey && e.key === 'ArrowLeft' && prev) window.location.href = root + prev;
    if (e.altKey && e.key === 'ArrowRight' && next) window.location.href = root + next;
  });
})();

// ── 4. Copy-to-clipboard on code blocks ──────────────────────────────
(function() {
  document.querySelectorAll('pre').forEach(function(pre) {
    var btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    pre.appendChild(btn);
    btn.addEventListener('click', function() {
      var code = pre.querySelector('code');
      var text = code ? code.innerText : pre.innerText;
      // Remove the button text from the copy
      text = text.replace(/\nCopy$/, '').replace(/^Copy\n/, '');
      navigator.clipboard.writeText(text).then(function() {
        btn.textContent = 'Copied ✓';
        btn.classList.add('copied');
        setTimeout(function() { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
      }).catch(function() {
        btn.textContent = 'Error';
        setTimeout(function() { btn.textContent = 'Copy'; }, 1500);
      });
    });
  });
})();

// ── 5. Dark mode toggle ───────────────────────────────────────────────
(function() {
  var stored = localStorage.getItem('rdv2-theme');
  if (stored === 'dark') document.documentElement.setAttribute('data-theme', 'dark');

  var btn = document.createElement('button');
  btn.className = 'theme-toggle';
  btn.setAttribute('aria-label', 'Toggle dark mode');
  btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀' : '🌙';

  btn.addEventListener('click', function() {
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('rdv2-theme', 'light');
      btn.textContent = '🌙';
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('rdv2-theme', 'dark');
      btn.textContent = '☀';
    }
  });

  var headerLinks = document.querySelector('.site-header-links');
  if (headerLinks) headerLinks.insertBefore(btn, headerLinks.firstChild);
})();

// ── 6. Back-to-top button ─────────────────────────────────────────────
(function() {
  var btn = document.createElement('button');
  btn.className = 'back-to-top';
  btn.setAttribute('aria-label', 'Back to top');
  btn.textContent = '↑';
  document.body.appendChild(btn);

  window.addEventListener('scroll', function() {
    btn.classList.toggle('visible', window.scrollY > 300);
  }, { passive: true });

  btn.addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

// ── 7. Client-side search (lunr.js, lazy-loaded) ─────────────────────
(function() {
  var input = document.getElementById('site-search');
  var resultsEl = document.getElementById('search-results');
  if (!input || !resultsEl) return;

  var lunrLoaded = false;
  var indexData = null;
  var lunrIndex = null;

  var root = '';
  var navA = document.querySelector('.nav-list li a');
  if (navA) {
    var rel = navA.getAttribute('href') || '';
    var ups = (rel.match(/\.\.\//g) || []).length;
    for (var i = 0; i < ups; i++) root += '../';
  }

  function loadLunr(cb) {
    if (lunrLoaded) { cb(); return; }
    var s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/lunr@2.3.9/lunr.min.js';
    s.onload = function() { lunrLoaded = true; cb(); };
    document.head.appendChild(s);
  }

  function buildIndex(data) {
    indexData = data;
    lunrIndex = lunr(function() {
      this.ref('id');
      this.field('title', { boost: 10 });
      this.field('body');
      data.forEach(function(doc) { this.add(doc); }, this);
    });
  }

  function escapeHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function showResults(query) {
    resultsEl.innerHTML = '';
    if (!query || query.length < 2) { resultsEl.style.display = 'none'; return; }
    if (!lunrIndex) { return; }
    try {
      var results = lunrIndex.search(query + '~1').slice(0, 8);
      if (!results.length) {
        resultsEl.innerHTML = '<div class="search-no-results">No results for “' + escapeHtml(query) + '”</div>';
        resultsEl.style.display = 'block';
        return;
      }
      results.forEach(function(r) {
        var doc = indexData.find(function(d) { return d.id === r.ref; });
        if (!doc) return;
        var item = document.createElement('a');
        item.href = root + doc.url;
        item.className = 'search-result-item';
        item.innerHTML =
          '<div class="search-result-title">' + escapeHtml(doc.title) + '</div>' +
          '<div class="search-result-body">' + escapeHtml(doc.body.slice(0, 90)) + '…</div>';
        resultsEl.appendChild(item);
      });
      resultsEl.style.display = 'block';
    } catch(e) { resultsEl.style.display = 'none'; }
  }

  input.addEventListener('focus', function() {
    loadLunr(function() {
      if (indexData) { showResults(input.value.trim()); return; }
      fetch(root + 'search-index.json')
        .then(function(r) { return r.json(); })
        .then(function(data) { buildIndex(data); showResults(input.value.trim()); })
        .catch(function(e) { console.error('search-index load failed', e); });
    });
  });

  var debounce = null;
  input.addEventListener('input', function() {
    clearTimeout(debounce);
    var q = input.value.trim();
    debounce = setTimeout(function() { showResults(q); }, 150);
  });

  document.addEventListener('click', function(e) {
    if (!input.contains(e.target) && !resultsEl.contains(e.target)) {
      resultsEl.style.display = 'none';
    }
  });

  input.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') { resultsEl.style.display = 'none'; input.blur(); }
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === '/' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      input.focus();
      input.select();
    }
  });
})();
"""
    (DST / "site.js").write_text(js, encoding="utf-8")
    print("  wrote: site.js (inline fallback)")


def build_search_index():
    """Generate search-index.json from all top-level HTML pages."""
    PAGES_ORDER = [
        ("09-Concepts-Primer.html",           "Radar Primer (101)"),
        ("00-Index.html",                      "Index / Overview"),
        ("01-System-Overview.html",            "System Overview"),
        ("02-Physics-and-Waveform.html",       "Physics & Waveform"),
        ("03-Beamforming-and-Scan.html",       "Beamforming & Scan"),
        ("04-Signal-Processing-Pipeline.html", "Signal Processing Pipeline"),
        ("05-Node-Architecture.html",          "Node Architecture"),
        ("06-Message-Catalog.html",            "Message Catalog"),
        ("07-Detection-and-Tracking.html",     "Detection & Tracking"),
        ("08-Scenarios-and-Targets.html",      "Scenarios & Targets"),
        ("10-Radar-Model-Library.html",        "Radar Model Library"),
        ("11-Multi-Radar-Fusion.html",         "Multi-Radar Fusion"),
        ("12-3D-Scene.html",                   "3-D Scene"),
        ("13-Reference-Tables.html",           "Reference Tables"),
        ("FUTURE-DEVELOPMENT.html",            "Future Development"),
    ]
    index = []
    for filename, title in PAGES_ORDER:
        dst_file = DST / filename
        if not dst_file.exists():
            continue
        raw = dst_file.read_text(encoding="utf-8")
        m = re.search(r'class="markdown-preview-section"[^>]*>(.*?)</div>', raw, re.DOTALL)
        text = ""
        if m:
            text = re.sub(r'<[^>]+>', ' ', m.group(1))
            text = re.sub(r'\s+', ' ', text).strip()[:400]
        doc_id = filename.replace(".html", "")
        index.append({"id": doc_id, "title": title, "url": filename, "body": text})
    (DST / "search-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("  wrote: search-index.json")


def _read_asset(name: str) -> str:
    """Read site asset from alongside build.py, falling back to DST."""
    candidates = [Path(__file__).parent / name, DST / name]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Asset not found: {name}")


def write_site_css():
    src = Path(__file__).parent / "site.css"
    dst = DST / "site.css"
    if src.resolve() == dst.resolve():
        print("  skipped: site.css (already in place)")
        return
    content = _read_asset("site.css")
    dst.write_text(content, encoding="utf-8")
    print("  wrote: site.css")


def _write_site_css_inline():
    css = """\
/* radarv2-docs — Slate + Indigo theme */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --sidebar-width: 260px;
  --header-height: 52px;
  /* NOTE: --color-text-muted updated to #374151 for better readability */

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
  align-items: center;
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
.sidebar-footer a { color: var(--color-text-subtle); text-decoration: none; }
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
  position: relative;
}
pre code {
  background: none;
  border: none;
  padding: 0;
  color: #e2e8f0;
  font-size: 13px;
}

/* ── Copy button ── */
.copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  color: #94a3b8;
  font-size: 11px;
  font-family: var(--font-sans);
  padding: 3px 9px;
  border-radius: 4px;
  cursor: pointer;
  opacity: 0;
  transition: opacity .15s, background .15s;
}
pre:hover .copy-btn { opacity: 1; }
.copy-btn:hover { background: rgba(255,255,255,0.15); color: #e2e8f0; }
.copy-btn.copied { background: #16a34a; border-color: #16a34a; color: #fff; opacity: 1; }

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
.mermaid svg { width: 100% !important; height: 100% !important; max-width: none !important; display: block; }
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
.md-table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; font-family: var(--font-sans); }
.md-table th { background: var(--color-surface); padding: 8px 14px; text-align: left; font-weight: 600; color: var(--color-text); border: 1px solid var(--color-border); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
.md-table td { padding: 8px 14px; border: 1px solid var(--color-border-light); color: var(--color-text-muted); vertical-align: top; }
.md-table tr:hover td { background: var(--color-surface); }

/* ── Callouts ── */
.callout { border-radius: 6px; padding: 12px 16px; margin: 16px 0; border-left: 3px solid var(--color-primary); background: var(--color-primary-light); font-size: 14px; }
.callout-title { font-weight: 700; margin-bottom: 4px; color: var(--color-primary-dark); font-size: 13px; font-family: var(--font-sans); }
.callout-content { color: var(--color-text-muted); }
.callout-content p { color: var(--color-text-muted); margin-bottom: 4px; }
.callout[data-callout="warning"]  { border-color: #d97706; background: #fffbeb; }
.callout[data-callout="warning"] .callout-title  { color: #92400e; }
.callout[data-callout="danger"], .callout[data-callout="error"] { border-color: #dc2626; background: #fef2f2; }
.callout[data-callout="danger"] .callout-title, .callout[data-callout="error"] .callout-title { color: #991b1b; }
.callout[data-callout="info"]     { border-color: #0ea5e9; background: #f0f9ff; }
.callout[data-callout="info"] .callout-title    { color: #0369a1; }
.callout[data-callout="note"]     { border-color: #16a34a; background: #f0fdf4; }
.callout[data-callout="note"] .callout-title    { color: #15803d; }
.callout[data-callout="abstract"] { border-color: #0ea5e9; background: #f0f9ff; }
.callout[data-callout="abstract"] .callout-title { color: #0369a1; }
.callout[data-callout="tip"]      { border-color: #16a34a; background: #f0fdf4; }
.callout[data-callout="tip"] .callout-title     { color: #15803d; }

/* ── Internal links ── */
.internal-link { color: var(--color-primary); text-decoration: none; border-bottom: 1px solid #c7d2fe; }
.internal-link:hover { color: var(--color-primary-dark); border-bottom-color: var(--color-primary); text-decoration: none; }
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

/* ── Right-side TOC ── */
.page-toc {
  position: fixed;
  top: var(--header-height);
  right: 0;
  width: 220px;
  padding: 20px 14px;
  height: calc(100vh - var(--header-height));
  overflow-y: auto;
  border-left: 1px solid var(--color-border-light);
  background: var(--color-bg);
  z-index: 50;
  scrollbar-width: thin;
}
.page-toc-title {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--color-text-subtle);
  margin-bottom: 10px;
  font-family: var(--font-sans);
}
.toc-link {
  display: block;
  font-size: 12px;
  color: var(--color-text-subtle);
  text-decoration: none;
  padding: 3px 0 3px 10px;
  border-left: 2px solid transparent;
  transition: all .1s;
  line-height: 1.4;
  font-family: var(--font-sans);
}
.toc-link:hover { color: var(--color-primary); border-left-color: var(--color-primary); text-decoration: none; }
.toc-link.toc-active { color: var(--color-primary); border-left-color: var(--color-primary); font-weight: 600; }
.toc-link.toc-h3 { padding-left: 20px; font-size: 11px; }
.has-toc .main-content { margin-right: 220px; }
@media (max-width: 1100px) {
  .page-toc { display: none; }
  .has-toc .main-content { margin-right: 0; }
}

/* ── Dark mode toggle button ── */
.theme-toggle {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.2);
  color: rgba(255,255,255,0.7);
  font-size: 14px;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
  margin-right: 4px;
  flex-shrink: 0;
}
.theme-toggle:hover { background: rgba(255,255,255,0.12); color: #fff; }

/* ── Dark mode variables ── */
[data-theme="dark"] {
  --color-bg:            #0f172a;
  --color-surface:       #1e293b;
  --color-surface-alt:   #273549;
  --color-border:        #334155;
  --color-border-light:  #1e293b;
  --color-text:          #e2e8f0;
  --color-text-muted:    #94a3b8;
  --color-text-subtle:   #64748b;
  --color-primary-light: #1e1b4b;
  --color-primary-bg:    #1e1b4b;
}
[data-theme="dark"] pre { background: #020617; }
[data-theme="dark"] .site-header { background: #0f0e2e; }
[data-theme="dark"] .sidebar { background: #0f172a; }
[data-theme="dark"] .page-toc { background: #0f172a; }
[data-theme="dark"] .mermaid-hint { background: rgba(15,23,42,0.9); }
[data-theme="dark"] #site-search { background: #1e293b; color: #e2e8f0; border-color: #334155; }
[data-theme="dark"] .search-results { background: #1e293b; border-color: #334155; }
[data-theme="dark"] .search-result-title { color: #e2e8f0; }
[data-theme="dark"] .search-result-item:hover { background: #1e1b4b; }
[data-theme="dark"] .doc-pager a { border-color: #334155; }
[data-theme="dark"] .doc-pager a:hover { background: #1e1b4b; border-color: var(--color-primary); }

/* ── Back-to-top ── */
.back-to-top {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  border: none;
  font-size: 18px;
  cursor: pointer;
  opacity: 0;
  transform: translateY(8px);
  transition: opacity .2s, transform .2s;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(79,70,229,0.4);
  line-height: 1;
}
.back-to-top.visible { opacity: 1; transform: translateY(0); }
.back-to-top:hover { background: var(--color-primary-dark); }

/* ── Prev/Next pager ── */
.doc-pager {
  display: flex;
  justify-content: space-between;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-light);
  gap: 12px;
}
.doc-pager a {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 18px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  text-decoration: none;
  flex: 1;
  max-width: 48%;
  transition: all .15s;
}
.pager-prev { text-align: left; }
.pager-next { text-align: right; margin-left: auto; }
.doc-pager a:hover { border-color: var(--color-primary); background: var(--color-primary-bg); text-decoration: none; }
.pager-label { font-size: 11px; color: var(--color-text-subtle); text-transform: uppercase; letter-spacing: .06em; font-family: var(--font-sans); display: block; }
.pager-title { font-size: 13px; font-weight: 600; color: var(--color-primary); font-family: var(--font-sans); display: block; }

/* ── Search ── */
.sidebar-search { margin-top: 10px; position: relative; }
#site-search {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 12px;
  font-family: var(--font-sans);
  background: var(--color-bg);
  color: var(--color-text);
  outline: none;
  transition: border-color .15s, box-shadow .15s;
}
#site-search:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(79,70,229,0.15); }
#site-search::placeholder { color: var(--color-text-subtle); }
.search-results {
  display: none;
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 500;
  max-height: 380px;
  overflow-y: auto;
}
.search-result-item {
  display: block;
  padding: 10px 12px;
  text-decoration: none;
  border-bottom: 1px solid var(--color-border-light);
  transition: background .1s;
}
.search-result-item:last-child { border-bottom: none; }
.search-result-item:hover { background: var(--color-primary-bg); text-decoration: none; }
.search-result-title { font-size: 13px; font-weight: 600; color: var(--color-text); font-family: var(--font-sans); }
.search-result-body { font-size: 11px; color: var(--color-text-subtle); margin-top: 2px; font-family: var(--font-sans); line-height: 1.4; }
.search-no-results { padding: 12px; font-size: 13px; color: var(--color-text-subtle); font-family: var(--font-sans); text-align: center; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .main-content { margin-left: 0; }
  .markdown-preview-section { padding: 24px 20px 60px; }
  .site-subtitle { display: none; }
  .back-to-top { bottom: 16px; right: 16px; }
}
"""
    (DST / "site.css").write_text(css, encoding="utf-8")
    print("  wrote: site.css (inline fallback)")


def write_index():
    html = ('<!DOCTYPE html>\n<html><head><meta charset="UTF-8">'
            '<meta http-equiv="refresh" content="0;url=00-Index.html">'
            '<title>radarv2 docs</title></head>'
            '<body><a href="00-Index.html">Go to index</a></body></html>\n')
    (DST / "index.html").write_text(html, encoding="utf-8")
    print("  wrote: index.html")


def main():
    parser = argparse.ArgumentParser(description="Build radarv2-docs GitHub Pages site")
    parser.add_argument('--src', default='/home/berkay/projects/aros-private/vault/radarv2',
                        help='Source vault directory')
    parser.add_argument('--dst', default='/home/berkay/projects/radarv2-docs',
                        help='Output site directory')
    args = parser.parse_args()

    global SRC, DST
    SRC = Path(args.src)
    DST = Path(args.dst)

    print(f"Building radarv2-docs site...\n  src: {SRC}\n  dst: {DST}")
    write_site_css()
    write_site_js()
    write_index()

    for src_file in sorted(SRC.rglob("*")):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(SRC)
        if src_file.suffix == ".html":
            process_html(src_file, rel)
        elif src_file.suffix in (".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico"):
            copy_binary(src_file, rel)

    build_search_index()
    print("Done.")


if __name__ == "__main__":
    main()
