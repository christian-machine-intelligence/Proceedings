/* The Word before creation: one of the engraved scenes in scenes.json over the waters, drawn in the brand's field across the whole
   footer. Each scene's field (scripts/illus/engrave.py --field) gives every cell the angle of the form, how strongly it
   follows the form, and its tone. Outside the drawing the strokes follow the ground's slow flow. Where the drawing rises
   past the top of the footer it carries on over the page as a negative (thread on linen) and thins out. When the footer
   first comes into view the drawing gathers out of the moving field, spreading from the scene's centre; then it holds
   still, and only the waters move. The scene's verse rides just above the horizon. */
(async (BASE) => {
  const SCENES = await (await fetch(new URL('scenes.json', BASE))).json();   // one entry per scene; scripts/illus/footer_scene.py adds them
  const qs = new URLSearchParams(location.search), names = Object.keys(SCENES);
  let pick = qs.get('scene');
  if (!SCENES[pick]) {
    let last = null; try { last = sessionStorage.getItem('icmi-scene'); } catch (e) {}
    const pool = names.filter(n => n !== last);
    pick = pool[Math.floor(Math.random() * pool.length)];
  }
  try { sessionStorage.setItem('icmi-scene', pick); } catch (e) {}
  const S = SCENES[pick];
  const links = document.getElementById('links');
  if (links) links.innerHTML = names.map(n => `<a href="?scene=${n}">${SCENES[n].ref}</a>`).join(' · ');
  const verse = document.getElementById('verse');
  verse.innerHTML = `${S.verse} <span>${S.ref}</span>`;
  const cv = document.getElementById('word'), ctx = cv.getContext('2d'), foot = cv.parentElement;
  cv.setAttribute('aria-label', `An engraving: ${S.label}.`);

  const img = new Image(); img.src = new URL(`${pick}.png`, BASE); await img.decode();
  const FW = img.width, FH = img.height, oc = document.createElement('canvas'); oc.width = FW; oc.height = FH;
  const ox = oc.getContext('2d'); ox.drawImage(img, 0, 0); const F = ox.getImageData(0, 0, FW, FH).data;

  const THREAD = [0x2E, 0x32, 0x36], LINEN = [0xE8, 0xE8, 0xE2];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const R0 = mulberry(11), TERMS = [0, 1, 2, 3].map(() => ({ fx: 2 + 4 * R0(), fy: 2 + 4 * R0(), ph: 6.28 * R0() }));
  const flow = (x, y) => TERMS.reduce((s, q) => s + Math.sin(q.fx * x + q.fy * y + q.ph), 0) * 0.55;
  const smooth = x => { x = Math.min(Math.max(x, 0), 1); return x * x * (3 - 2 * x); };

  let GROUND = LINEN, CLIP = 0;
  function groundAbove() {                       // the colour of the block just above the footer, and where it begins
    const solid = el => { const m = getComputedStyle(el).backgroundColor.match(/[\d.]+/g); return m && (m.length < 4 || +m[3] > 0.5) ? m.slice(0, 3).map(Number) : null; };
    let el = foot.previousElementSibling, c = null;
    while (el && !el.offsetHeight) el = el.previousElementSibling;   // skip anything hidden
    while (el && !(c = solid(el)) && el.lastElementChild) el = el.lastElementChild;
    const fr = foot.getBoundingClientRect();
    if (c) { GROUND = c; CLIP = Math.max(0, L - (fr.top - el.getBoundingClientRect().top)); }
    else { GROUND = solid(document.body) || LINEN; CLIP = 0; }   // rows above CLIP belong to another block: leave them alone
  }
  let W, H, L, cell, N, X, Y, U, V, FA, WT, TN, DL, dpr;
  function layout() {
    dpr = Math.min(devicePixelRatio || 1, 2);
    W = cv.clientWidth; H = cv.clientHeight; L = H - foot.clientHeight;          // L: how far the canvas rises above the footer
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    cell = Math.max(4, W / 360);
    const cols = Math.ceil(W / cell), rows = Math.ceil(H / cell); N = cols * rows;
    let sc, offX, offY;
    if (W < 760) {                                                          // phone: the scene fills a stage of its own
      const st = foot.querySelector('.stage').getBoundingClientRect(), fb = foot.getBoundingClientRect();
      sc = 2.2 * W / FW; offX = (W - FW * sc) * 0.85; offY = st.top - fb.top + L - 0.02 * FH * sc;
    } else { sc = Math.max(W / FW, H / FH); offX = (W - FW * sc) * 0.5; offY = 0; }
    // the scene's verse sits just above its horizon
    const hz = offY + S.sea * FH * sc - L;
    if (W >= 760) verse.style.top = `${Math.round(hz - verse.offsetHeight - 14)}px`; else verse.style.top = '';
    groundAbove();
    X = new Float32Array(N); Y = new Float32Array(N); U = new Float32Array(N); V = new Float32Array(N);
    FA = new Float32Array(N); WT = new Float32Array(N); TN = new Float32Array(N); DL = new Float32Array(N);
    const fx0 = S.from[0] * FW * sc + offX, fy0 = S.from[1] * FH * sc + offY;
    for (let i = 0; i < N; i++) {
      const x = (i % cols + 0.5) * cell, y = ((i / cols | 0) + 0.5) * cell;
      X[i] = x; Y[i] = y;
      const u = Math.min(FW - 1, Math.max(0, Math.floor((x - offX) / sc))), v = Math.min(FH - 1, Math.max(0, Math.floor((y - offY) / sc)));
      U[i] = u / FW; V[i] = v / FH;
      const k = 4 * (v * FW + u);
      FA[i] = F[k] / 255 * Math.PI; WT[i] = F[k + 1] / 255; TN[i] = F[k + 2] / 255;
      DL[i] = Math.hypot(x - fx0, y - fy0) / Math.max(W, H) * 3 + Math.random() * 0.3;
    }
  }
  const LV = 14, dark = [], light = [];
  const shade = (a, b, v) => `rgb(${a.map((c, j) => Math.round(c + (b[j] - c) * v))})`;
  function draw(t, born) {
    ctx.clearRect(0, 0, W, H);
    for (let l = 0; l < LV; l++) { dark[l] = new Path2D(); light[l] = new Path2D(); }
    const drift = t * 0.018;
    for (let i = 0; i < N; i++) {
      const k = born === null ? 1 : smooth((born - DL[i]) / 1.6);
      const sea = smooth((V[i] - S.sea) / 0.04);
      const ga = flow(X[i] / W * 2.2 + drift, Y[i] / W * 2.2 - drift * 0.5) + 0.12 * Math.sin(t * 0.5 + X[i] / W * 9);
      const w = WT[i] * k, d = ((FA[i] - ga + Math.PI / 2) % Math.PI + Math.PI) % Math.PI - Math.PI / 2;
      const swell = Math.sin(t * 0.9 - U[i] * 16 + V[i] * 46), glint = Math.sin(t * 1.3 + U[i] * 11 - V[i] * 70);
      const a = ga + d * w + 0.16 * swell * sea * k;
      const tone = TN[i] * k * (1 + 0.32 * glint * sea) * (W < 760 ? 1 - 0.5 * sea : 1);   // calmer waters behind a phone's type
      if (Y[i] < CLIP) continue;
      const above = Y[i] < L;                                               // over the page, not the footer
      // over the page only the drawing itself shows, thinning out as it rises
      const v = above ? 0.62 * tone * smooth((Y[i] - CLIP) / (L - CLIP)) * smooth((WT[i] - 0.15) / 0.3) : 0.24 + 0.6 * tone;
      if (v < 0.03) continue;
      const lv = Math.min(LV - 1, Math.round(v / 0.84 * (LV - 1)));
      const h = cell * (0.55 + 0.75 * tone) / 2, dx = h * Math.cos(a), dy = h * Math.sin(a);
      const p = (above ? dark : light)[lv]; p.moveTo(X[i] - dx, Y[i] - dy); p.lineTo(X[i] + dx, Y[i] + dy);
    }
    for (let l = 0; l < LV; l++) {
      const v = l / (LV - 1) * 0.84;
      ctx.lineWidth = Math.max(0.7, cell * (0.06 + 0.2 * Math.max(0, (v - 0.24) / 0.6)));
      ctx.strokeStyle = shade(THREAD, LINEN, v); ctx.stroke(light[l]);
      ctx.lineWidth = Math.max(0.7, cell * (0.06 + 0.2 * v / 0.84));
      ctx.strokeStyle = shade(GROUND, THREAD, v); ctx.stroke(dark[l]);
    }
  }
  await document.fonts.ready;
  layout(); verse.style.opacity = 1;
  let resizeT; addEventListener('resize', () => { clearTimeout(resizeT); resizeT = setTimeout(() => { layout(); if (reduce) draw(0, null); }, 150); });
  if (reduce) { draw(0, null); return; }
  let visible = false, t0 = null, last = 0;
  new IntersectionObserver(e => { visible = e[0].isIntersecting; if (visible && t0 === null) t0 = performance.now(); }, { threshold: 0.15 }).observe(cv);
  draw(0, -1);
  (function frame(now) {
    requestAnimationFrame(frame);
    if (!visible || now - last < 33) return;
    last = now; draw(now / 1000, t0 === null ? -1 : (now - t0) / 1000);
  })(0);
})(document.currentScript.src);
