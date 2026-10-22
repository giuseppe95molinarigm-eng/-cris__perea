(function () {
  const MM = 96 / 25.4;
  function sizeFigs(page) {
    const zone = page.querySelector('.figzone');
    if (!zone) return true;
    const rows = [...zone.querySelectorAll('.figrow')];
    const cs = getComputedStyle(zone);
    const zoneH = zone.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - (rows.length - 1) * parseFloat(cs.rowGap || 0);
    const rowH = zoneH / rows.length; zone.dataset.dbg = Math.round(zone.clientHeight) + '/' + Math.round(zoneH);
    let ok = true;
    for (const row of rows) {
      const figs = [...row.querySelectorAll('.fig')];
      const n = figs.length;
      const gap = parseFloat(getComputedStyle(row).columnGap || 0);
      const W = (row.clientWidth - gap * (n - 1)) / n;
      // provisional width to measure captions
      figs.forEach(f => { f.style.width = W + 'px'; });
      const capH = Math.max(0, ...figs.map(f => { const c = f.querySelector('.cap'); return c ? c.offsetHeight + 3 * MM : 0; }));
      const H = Math.min((rowH - capH) * 0.95, (n === 1 ? 140 : 122) * MM);
      if (H < 55 * MM) ok = false;
      // common height so frames line up
      let h = H;
      figs.forEach(f => {
        const ar = parseFloat(f.querySelector('.frame').dataset.ar);
        h = Math.min(h, W / ar);
      });
      figs.forEach(f => {
        const fr = f.querySelector('.frame');
        const ar = parseFloat(fr.dataset.ar);
        let w = Math.min(W, h * ar);
        if (fr.classList.contains('arch')) w = Math.min(W, Math.max(w, h * 0.62));
        fr.style.width = w + 'px'; fr.style.height = h + 'px';
        f.style.width = Math.max(w, Math.min(W, 46 * MM)) + 'px';
      });
    }
    return ok;
  }
  function overflowing(page) {
    const c = page.querySelector('.content') || page.querySelector('.toc');
    const t = page.querySelector('.trim');
    if (!c) return false;
    const tb = t.getBoundingClientRect();
    const limit = tb.bottom - 17 * MM;
    let maxB = 0;
    c.querySelectorAll('*').forEach(e => { const r = e.getBoundingClientRect(); if (r.height) maxB = Math.max(maxB, r.bottom); });
    return maxB > limit + 1 || c.scrollHeight > c.clientHeight + 1;
  }
  function fit() {
    const bad = [];
    document.querySelectorAll('.page').forEach(p => {
      for (const lvl of ['', 'tight', 'tighter']) {
        if (lvl) p.classList.add(lvl);
        const ok = sizeFigs(p);
        if (ok && !overflowing(p)) return;
      }
      if (overflowing(p)) { p.dataset.overflow = '1'; bad.push(p.dataset.p); }
    });
    document.body.dataset.overflow = bad.join(',');
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit); else window.addEventListener('load', fit);
})();
