/* HH Next-Level Epoxy — site motion (pairs with motion.css)
   - reveals sections and cards as they scroll into view, staggered
   - counts the hero/about stats up from zero
   - reading-progress bar on blog posts
   Does nothing when the visitor has asked for reduced motion. */
(function () {
  if (!window.matchMedia || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  /* ── Scroll reveal ── */
  var GROUPS = [
    // [selector, extra class]
    ['.section-inner>.lbl,.section-inner>.lbl2,.section-inner>.stitle,.section-inner>.slead,.section-inner>h2,.section-inner>p', ''],
    ['.trust-bar .ti,.about-content>*,.feat-content>*,.rev-header,.cta-band>*,.cta-inline,.info-section .section-inner>*', ''],
    ['.svc-grid>*,.why-grid>*,.proc-steps>*,.gallery-grid>*,.colors-grid>*,.rev-grid>*,.card-grid>*,.hub-grid>*,' +
     '.area-grid>*,.link-grid>*,.about-stats>*,.info-grid>*,.bio-grid>*,.contact-grid>*,.error-links>*,.why-cards>*', 'hh-zoom'],
    ['.areas-pills>*', 'hh-zoom'],
    ['.about-img-wrap,.feat-img', 'hh-left'],
    ['.cbody>*,.article-body>*,.c2>aside>*,.sb-cta,.sb-info,.faq-item,.calc-card,.gallery-masonry>*', '']
  ];

  var vh = window.innerHeight || document.documentElement.clientHeight;
  var targets = [];
  GROUPS.forEach(function (g) {
    var els = document.querySelectorAll(g[0]);
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el.classList.contains('hh-r') || el.closest('.hh-r')) continue;   // don't nest reveals
      if (el.closest('.hero,.hero-int,.article-hero,.error-hero,footer,nav,.mobile-drawer')) continue;
      var r = el.getBoundingClientRect();
      if (r.top < vh * 0.92 && r.bottom > 0) continue;                      // already on screen: leave it alone
      el.classList.add('hh-r');
      if (g[1]) el.classList.add(g[1]);
      targets.push(el);
    }
  });

  function finish(el) {
    el.classList.remove('hh-r', 'hh-in', 'hh-zoom', 'hh-left', 'hh-right');
    el.style.removeProperty('--hh-d');
  }

  if ('IntersectionObserver' in window && targets.length) {
    var io = new IntersectionObserver(function (entries) {
      var shown = entries.filter(function (e) { return e.isIntersecting; })
        .map(function (e) { return e.target; })
        .sort(function (a, b) { return a.compareDocumentPosition(b) & 4 ? -1 : 1; });
      var perParent = new Map();
      shown.forEach(function (el) {
        // stagger siblings (cards in one grid), not everything on screen
        var i = perParent.get(el.parentElement) || 0;
        perParent.set(el.parentElement, i + 1);
        io.unobserve(el);
        el.style.setProperty('--hh-d', Math.min(i * 0.09, 0.45) + 's');
        el.classList.add('hh-in', 'hh-seen');
        // hand control back to the element's own hover transitions once revealed
        setTimeout(function () { finish(el); }, 900 + Math.min(i * 90, 450));
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    targets.forEach(function (el) { io.observe(el); });
  } else {
    targets.forEach(finish);
  }

  /* ── Count-up stats ── */
  function countUp(el, delay) {
    var txt = el.textContent, m = txt.match(/^(\s*)(\d+)(.*)$/s);
    if (!m) return;
    var end = parseInt(m[2], 10);
    if (end < 2) return;                       // "1-Day" stays as is
    var start = null, dur = 1400;
    el.textContent = m[1] + '0' + m[3];
    setTimeout(function () {
      requestAnimationFrame(function step(t) {
        if (start === null) start = t;
        var p = Math.min((t - start) / dur, 1), e = 1 - Math.pow(1 - p, 3);
        el.textContent = m[1] + Math.round(end * e) + m[3];
        if (p < 1) requestAnimationFrame(step); else el.textContent = txt;
      });
    }, delay || 0);
  }
  var heroNums = document.querySelectorAll('.hero-trust .ht-num');
  for (var h = 0; h < heroNums.length; h++) countUp(heroNums[h], 700);

  var statNums = document.querySelectorAll('.stat-num');
  if ('IntersectionObserver' in window && statNums.length) {
    var so = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { so.unobserve(e.target); countUp(e.target, 250); }
      });
    }, { threshold: 0.6 });
    for (var s = 0; s < statNums.length; s++) so.observe(statNums[s]);
  }

  /* ── Reading progress on blog posts ── */
  var article = document.querySelector('.article-body');
  if (article) {
    var bar = document.createElement('div');
    bar.className = 'hh-progress';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
    var ticking = false;
    var update = function () {
      ticking = false;
      var r = article.getBoundingClientRect();
      var total = r.height - window.innerHeight * 0.6;
      var p = total > 0 ? Math.min(Math.max(-r.top / total, 0), 1) : 1;
      bar.style.transform = 'scaleX(' + p + ')';
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }
})();
