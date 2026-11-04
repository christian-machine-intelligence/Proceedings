/* Each paper's engraving, drawn live: the same field of short strokes as the footer, thread on linen. The strokes
   follow the ground's slow flow; when the engraving comes into view the paper's drawing gathers out of it, spreading
   from the drawing's centre, and then only the ground keeps drifting.

   <div class="engrave" data-field="art/field/band-29.png" data-seed="399"></div>
   The field PNG (scripts/illus/engrave.py --field) gives every cell its angle along the form (R), how strongly it
   follows the form (G), its tone (B) and the ground's strength (A). CSS on the element places and fades it:
     --ax     where the field sits across the element when it is cropped: 0 left, 0.5 centre, 1 right
     --shift  px to move it further right
     --fade   none | left (comes in from the left, clear for type) | edges (dissolves into the page all round) */
(() => {
  const LINEN = [0xE8, 0xE8, 0xE2], THREAD = [0x2E, 0x32, 0x36], LV = 12;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const smooth = x => { x = Math.min(Math.max(x, 0), 1); return x * x * (3 - 2 * x); };
  const shade = v => `rgb(${LINEN.map((c, j) => Math.round(c + (THREAD[j] - c) * v))})`;
  function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function flowFor(seed) {                           // as flow_for in engrave.py, so the ground starts where the still is
    const R = mulberry(seed), T = [0, 1, 2, 3].map(() => ({ fx: 2 + 4 * R(), fy: 2 + 4 * R(), ph: 6.28 * R() }));
    return (x, y) => T.reduce((s, q) => s + Math.sin(q.fx * x + q.fy * y + q.ph), 0) * 0.55;
  }

  const live = [];
  function Engrave(host) {
    const cv = document.createElement('canvas'); cv.setAttribute('aria-hidden', 'true');
    host.appendChild(cv);
    const ctx = cv.getContext('2d'), flow = flowFor(+host.dataset.seed || 7);
    let F, FW, FH, W, H, N, X, Y, A, WT, TN, EF, DL, FD, visible = false, t0 = null, ready = false;

    function layout() {
      const dpr = Math.min(devicePixelRatio || 1, 2);
      W = host.clientWidth; H = host.clientHeight; if (!W || !H) return;
      cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const cs = getComputedStyle(host), ax = parseFloat(cs.getPropertyValue('--ax')) || 0.5,
            shift = parseFloat(cs.getPropertyValue('--shift')) || 0, fade = cs.getPropertyValue('--fade').trim() || 'none';
      const cell = Math.max(W / FW, H / FH), offX = (W - FW * cell) * ax + shift, offY = (H - FH * cell) / 2;
      N = 0; X = []; Y = []; A = []; WT = []; TN = []; EF = []; FD = []; DL = [];
      let cx = 0, cy = 0, cw = 0;
      for (let j = 0; j < FH; j++) for (let i = 0; i < FW; i++) {
        const x = offX + (i + 0.5) * cell, y = offY + (j + 0.5) * cell;
        if (x < -cell || x > W + cell || y < -cell || y > H + cell) continue;
        const k = 4 * (j * FW + i);
        let f = 1;
        if (fade === 'left') f = smooth((x / W - 0.42) / 0.26);
        else if (fade === 'edges') f = 1 - smooth((Math.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2)) - 0.58) / 0.42);
        if (f < 0.02) continue;
        X.push(x); Y.push(y); A.push(F[k] / 255 * Math.PI); WT.push(F[k + 1] / 255); TN.push(F[k + 2] / 255);
        EF.push(F[k + 3] / 255); FD.push(f); N++;
        const m = F[k + 1] / 255 * F[k + 2] / 255; cx += x * m; cy += y * m; cw += m;
      }
      cx /= cw || 1; cy /= cw || 1;
      for (let n = 0; n < N; n++) DL.push(Math.hypot(X[n] - cx, Y[n] - cy) / Math.max(W, H) * 2.4 + Math.random() * 0.3);
      host.cell = cell;
    }

    function draw(t, born) {
      if (!N) return;
      ctx.clearRect(0, 0, W, H);
      const paths = Array.from({ length: LV }, () => new Path2D()), drift = t * 0.018, cell = host.cell;
      for (let n = 0; n < N; n++) {
        const k = born === null ? 1 : smooth((born - DL[n]) / 1.6);
        const ga = flow(X[n] / W * 2.2 + drift, Y[n] / W * 2.2 - drift * 0.5) + 0.1 * Math.sin(t * 0.45 + X[n] / W * 8);
        const w = WT[n] * k, d = ((A[n] - ga + Math.PI / 2) % Math.PI + Math.PI) % Math.PI - Math.PI / 2;
        const tone = TN[n] * k, v = (0.26 * EF[n] + 0.6 * tone) * FD[n];
        if (v < 0.03) continue;
        const a = ga + d * w, h = cell * (0.55 + 0.75 * tone) / 2, dx = h * Math.cos(a), dy = h * Math.sin(a);
        const p = paths[Math.min(LV - 1, Math.round(v / 0.86 * (LV - 1)))];
        p.moveTo(X[n] - dx, Y[n] - dy); p.lineTo(X[n] + dx, Y[n] + dy);
      }
      for (let l = 0; l < LV; l++) {
        const v = l / (LV - 1) * 0.86;
        ctx.lineWidth = Math.max(0.6, cell * (0.06 + 0.2 * Math.max(0, (v - 0.26) / 0.6)));
        ctx.strokeStyle = shade(v); ctx.stroke(paths[l]);
      }
    }

    const img = new Image(); img.src = host.dataset.field;
    img.decode().then(() => {
      FW = img.width; FH = img.height;
      const oc = document.createElement('canvas'); oc.width = FW; oc.height = FH;
      const ox = oc.getContext('2d'); ox.drawImage(img, 0, 0); F = ox.getImageData(0, 0, FW, FH).data;
      layout(); ready = true; host.classList.add('live');
      if (reduce) draw(0, null); else draw(0, -1);
    });
    // the ground moves whenever any of it shows; the drawing only gathers once the reader has scrolled it well into view
    new IntersectionObserver(e => {
      const r = e[0]; visible = r.isIntersecting;
      const need = Math.min(0.6, 0.6 * innerHeight / Math.max(1, r.boundingClientRect.height));
      if (t0 === null && r.intersectionRatio >= need) t0 = performance.now();
    }, { threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6] }).observe(host);
    return {
      resize() { if (ready) { layout(); if (reduce) draw(0, null); } },
      frame(now) { if (ready && visible && !reduce) draw(now / 1000, t0 === null ? -1 : (now - t0) / 1000); },
    };
  }

  document.querySelectorAll('.engrave[data-field]').forEach(h => live.push(Engrave(h)));
  let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => live.forEach(e => e.resize()), 150); });
  if (reduce || !live.length) return;
  let last = 0;
  (function loop(now) { requestAnimationFrame(loop); if (now - last < 33) return; last = now; live.forEach(e => e.frame(now)); })(0);
})();
