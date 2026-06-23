// site.js — radarv2-docs interactive layer

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
