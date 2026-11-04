/* ICMI field. Draws the hero (#hero-field: a field of short strokes in which a scarlet thread is sewn, drawn into the
   crossing and out along both beams of a woven cross, then the four small crosses), the paper fields
   (canvas.paper-field[data-n], scarlet only on [data-current]) and the marks (span.mark[data-size][data-theme]).
   Type keeps a clearing: the hero leaves every [data-clear] element's area empty and sets the cross in the space left. */
(() => {
  "use strict";
  const PI = Math.PI, UP = PI / 2;
  const PAL = {
    light: { bg: "#E8E8E2", ink: "#2E3236", sc: "#B0222D" },
    dark:  { bg: "#2E3236", ink: "#E8E8E2", sc: "#E8524C" },
  };
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------- helpers
  const clamp = (x, a = 0, b = 1) => Math.min(Math.max(x, a), b);
  const ease = x => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
  const prog = (t, d, dur) => ease((t - d) / dur);
  const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
  const s01 = x => smooth(0, 1, x);
  // position over u in [0, 1] for a speed that eases in over the first a, holds, and eases out over the last b
  function glide(a, b, n = 400) {
    const P = [0];
    for (let k = 1; k <= n; k++) { const u = (k - 0.5) / n; P.push(P[k - 1] + s01(u / a) * s01((1 - u) / b)); }
    return u => { const x = clamp(u) * n, k = Math.min(n - 1, Math.floor(x)); return (P[k] + (P[k + 1] - P[k]) * (x - k)) / P[n]; };
  }
  const lerpA = (a, b, t) => { const d = (((b - a + PI / 2) % PI) + PI) % PI - PI / 2; return a + d * t; };
  const rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const mix = (a, b, w) => { const p = rgb(a), q = rgb(b); return `rgb(${p.map((v, i) => Math.round(v + (q[i] - v) * w))})`; };
  const odd = (x, y) => ((x + y) % 2 + 2) % 2 === 1;
  function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  // the ground's slow flow, which the needle follows
  function flowFor(seed) {
    const R0 = mulberry(seed), TERMS = [1, -1, 1, -2].map(k => ({ fx: 2 + 4 * R0(), fy: 2 + 4 * R0(), ph: 6.28 * R0(), k }));
    return (x, y) => TERMS.reduce((s, q) => s + Math.sin(q.fx * x + q.fy * y + q.ph), 0) * 0.55;
  }
  // a paper's number (1, 2 … or A–E) as a seed
  const seedOf = n => /^\d+$/.test(n) ? +n : 100 + String(n).toUpperCase().charCodeAt(0);
  // ---------- each paper's own sewing. The cross, its timing and its colours never change; what the paper's number
  // chooses is how the needle sews the thread through the field before drawing it into the crossing:
  //   the ground's flow and noise, which the needle follows;
  //   weft or warp: passes across the cross (as on the homepage) or up and down it;
  //   which corner the needle enters from;
  //   three, five or seven passes (always odd, so the middle pass runs through the crossing);
  //   where the thread dips under the cloth.
  // With no number, the homepage's sewing: five weft passes from the top left.
  function variant(n) {
    if (n === undefined || n === null || n === "") return { flow: 5, ground: 7, weave: 11, passes: 5, warp: false, fx: false, fy: false };
    // 3 pass counts × weft or warp × 4 corners = 24 sewings, stepped through by 7 so that neighbouring papers always
    // differ in passes, and papers 1–24 each have their own; past 24 they repeat on a different ground
    const k = seedOf(n), c = (k * 7) % 24;
    return { flow: k * 7919 + 5, ground: k * 7919 + 7, weave: k * 7919 + 11,
             passes: [3, 5, 7][c % 3], warp: Math.floor(c / 3) % 2 === 1, fx: Math.floor(c / 6) % 2 === 1, fy: Math.floor(c / 12) === 1 };
  }
  function sizeCanvas(cv, W, H) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), ctx = cv.getContext("2d");
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return ctx;
  }
  const segTo = (path, cell) => (cx, cy, a, len) => { const h = cell * len / 2, dx = h * Math.cos(a), dy = h * Math.sin(a);
    path.moveTo(cx - dx, cy + dy); path.lineTo(cx + dx, cy - dy); };

  // ---------- the plain cross, in cells, crossing at 0,0; group is "main" or the small cross's index
  function plainCross() {
    const B = [], add = (x0, x1, y0, y1, dir, group) => B.push({ x0, x1, y0, y1, dir, group });
    add(-2, 2, -15, 15, "v", "main"); add(-15, 15, -2, 2, "h", "main");
    const subs = [[9, -9], [9, 9], [-9, 9], [-9, -9]].map(([x, y], i) => ({ x, y, i, sd: Math.hypot(x, y) }));
    subs.forEach(s => { add(s.x - 1, s.x + 1, s.y - 3, s.y + 3, "v", s.i); add(s.x - 3, s.x + 3, s.y - 1, s.y + 1, "h", s.i); });
    return { B, subs };
  }

  // ---------- the hero
  // seconds: the thread is sewn through the field (needle0 + weave); from draw0 both its ends are drawn into the crossing
  // (reel) while the scarlet runs out along both beams (run); a ripple leaves the crossing at subs (ring cells a second)
  // and the small crosses lock in as it reaches them. Every movement starts and stops at zero speed, and each phase
  // begins as the last one settles.
  const T = { needle0: 0.5, weave: 3.9, draw0: 4.4, run: 1.9, reel: 1.7, subs: 5.6, ring: 12, end: 9.6 };
  const SEW = glide(0.1, 0.14), RUN = glide(0.22, 0.5);
  const drift = s => { const x = Math.max(0, s - T.end); return (x - 2.5 * (1 - Math.exp(-x / 2.5))) / 18; };   // the ground eases into its drift
  // one field: cv is its canvas, hero the element it fills (any [data-clear] inside is kept clear of strokes),
  // n the paper's number, or none for the homepage's own sewing
  function Field(cv, hero, n) {
  const S = variant(n), flow = flowFor(S.flow);
  const G = { seq: 0, last: null, conv: -1, running: false, visible: false };

  function buildHero() {
    const hr = hero.getBoundingClientRect(), W = hr.width, H = hr.height;
    if (W < 10 || H < 10) return false;
    const ctx = sizeCanvas(cv, W, H);
    const rel = el => { const r = el.getBoundingClientRect(); return { x0: r.left - hr.left, y0: r.top - hr.top, x1: r.right - hr.left, y1: r.bottom - hr.top }; };
    const clears = [...hero.querySelectorAll("[data-clear]")].map(rel);
    const winEl = hero.querySelector(".hero-window"), win = winEl ? rel(winEl) : { x0: 0, y0: 0, x1: 0, y1: 0 };
    // the cross takes the largest space beside the type: right of it, below it, above it or left of it
    const sides = [{ x0: win.x1, x1: W, y0: 0, y1: H }, { x0: 0, x1: W, y0: win.y1, y1: H },
                   { x0: 0, x1: W, y0: 0, y1: win.y0 }, { x0: 0, x1: win.x0, y0: 0, y1: H }];
    const fit = q => Math.min(q.x1 - q.x0, q.y1 - q.y0), free = sides.reduce((a, b) => fit(b) > fit(a) ? b : a);
    const cell = clamp(fit(free) / 35, 7, +(hero.dataset.cellMax || 16)), fx = (free.x0 + free.x1) / 2, fy = (free.y0 + free.y1) / 2;
    const xa = Math.ceil((cell / 2 - fx) / cell), xb = Math.floor((W - cell / 2 - fx) / cell);
    const ya = Math.ceil((cell / 2 - fy) / cell), yb = Math.floor((H - cell / 2 - fy) / cell);
    const cols = xb - xa + 1, F = plainCross(), rnd = mulberry(S.ground), m = cell * 0.75;
    const cleared = (px, py) => clears.some(q => px > q.x0 - m && px < q.x1 + m && py > q.y0 - m && py < q.y1 + m);
    Object.assign(G, { ctx, W, H, cell, fx, fy, F, xa, xb, ya, yb, cells: [], at: new Map() });
    G.idx = (x, y) => { const i = G.at.get((y - ya) * cols + (x - xa)); return i === undefined ? -1 : i; };
    for (let y = ya; y <= yb; y++) for (let x = xa; x <= xb; x++) {
      const j = (rnd() * 2 - 1) * 0.05, noise = rnd() * PI;            // draw these even when cleared, so the field is stable
      if (cleared(fx + x * cell, fy + y * cell)) continue;
      const ax = Math.abs(x), ay = Math.abs(y), inB = F.B.filter(b => x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1);
      const hasV = inB.some(b => b.dir === "v"), hasH = inB.some(b => b.dir === "h"), group = inB.length ? inB[0].group : null;
      // how far the scarlet must have run out from the crossing before each stroke forms; side threads a little behind
      let kV = Infinity, kH = Infinity;
      for (const b of inB) if (b.group === "main") { if (b.dir === "v") kV = ay + 0.8 * ax; else kH = ax + 0.8 * ay; }
      const cl = { x, y, j, noise, hasV, hasH, group, kV, kH, radial: Math.atan2(-y, x), dc: Math.hypot(x, y), ord: flow(x * 0.035, y * 0.035) };
      if (typeof group === "number") { const s = F.subs[group]; cl.sub = s; cl.u = Math.max(Math.abs(x - s.x), Math.abs(y - s.y)) / 3; }
      G.at.set((y - ya) * cols + (x - xa), G.cells.length); G.cells.push(cl);
    }
    G.dcMax = Math.max(...G.cells.map(cl => cl.dc));
    weave({ x0: Math.ceil((free.x0 - fx) / cell), x1: Math.floor((free.x1 - fx) / cell), y0: Math.ceil((free.y0 - fy) / cell), y1: Math.floor((free.y1 - fy) / cell) });
    return true;
  }

  // the scarlet: one thread sewn through the field's own nodes, then strands that run out from each crossing along both
  // beams. Like a weft: five passes over the cross's space that take the field's slope, turning at each side; the middle
  // pass runs straight through the crossing, so both ends can be drawn into it at once.
  function weave(R) {
    // sewn in a frame of its own (always weft, from the top left), then turned and mirrored into place
    const R0 = S.warp ? { x0: R.y0, x1: R.y1, y0: R.x0, y1: R.x1 } : R;
    const Rc = { x0: S.fx ? -R0.x1 : R0.x0, x1: S.fx ? -R0.x0 : R0.x1, y0: S.fy ? -R0.y1 : R0.y0, y1: S.fy ? -R0.y0 : R0.y1 };
    const place = ([u, v]) => { if (S.fx) u = -u; if (S.fy) v = -v; return S.warp ? [v, u] : [u, v]; };
    const rnd = mulberry(S.weave), yS = Rc.y0 + 2, yE = Rc.y1 - 2, mid = (S.passes - 1) / 2;
    const bands = Array.from({ length: S.passes }, (_, k) => k < mid ? yS * (1 - k / mid) : k > mid ? yE * (k - mid) / mid : 0);
    const xL = Rc.x0 + 3.5, xR = Rc.x1 - 3.5, pts = [];
    let x = Rc.x0 - 0.5, y = yS;
    bands.forEach((yk, k) => {
      const s = k % 2 ? -1 : 1, last = k === bands.length - 1, xe = last ? Rc.x1 + 0.5 : s > 0 ? xR : xL;
      while (s > 0 ? x < xe : x > xe) {
        const a = flow(x * 0.085, y * 0.085);
        y += 0.25 * clamp(-1.3 * s * Math.sin(a) * Math.cos(a) + 0.2 * (yk - y), -1, 1); x += 0.25 * s;
        pts.push([x, k === mid ? y * (1 - smooth(3.5, 1.5, Math.abs(x))) : y]);
      }
      if (k === mid) y = pts[pts.length - 1][1];
      if (!last) { const r = (bands[k + 1] - y) / 2, cy = y + r;          // the turn at the side
        for (let q = 0.05; q <= PI; q += 0.05) pts.push([xe + 3 * s * Math.sin(q), cy - r * Math.cos(q)]);
        x = xe; y = cy + r; }
    });
    const nodes = [], put = (x, y) => { let n = nodes.length;
      if (n && nodes[n - 1][0] === x && nodes[n - 1][1] === y) return;
      if (n > 1 && nodes[n - 2][0] === x && nodes[n - 2][1] === y) { nodes.pop(); return; }      // no back-and-forth
      if (n > 1 && Math.max(Math.abs(nodes[n - 2][0] - x), Math.abs(nodes[n - 2][1] - y)) === 1) nodes.pop();   // stairs become diagonals
      nodes.push([x, y]); };
    let sx = null, sy = null;                                             // snap with hysteresis: no one-node blips
    for (const [px, py] of pts.map(place)) {
      if (sx === null || Math.abs(px - sx) > 0.7) sx = Math.round(px);
      if (sy === null || Math.abs(py - sy) > 0.7) sy = Math.round(py);
      put(sx, sy);
    }
    const M = nodes.length, strand = [], ic = nodes.findIndex(([x, y]) => x === 0 && y === 0);
    const arms = (cx, cy, n, g) => {                                       // a crossing and its four arms, by distance out from it
      const add = (x, y, dir, d) => { nodes.push([x, y]); strand.push({ dir, d, g, end: d === n }); };
      add(cx, cy, "v", 0); add(cx, cy, "h", 0);
      for (let d = 1; d <= n; d++) { add(cx, cy - d, "v", d); add(cx, cy + d, "v", d); add(cx - d, cy, "h", d); add(cx + d, cy, "h", d); }
    };
    arms(0, 0, 15, "main");
    G.F.subs.forEach(q => arms(q.x, q.y, 3, q.i));
    const N = nodes.length, dist = (a, b) => Math.hypot(nodes[a][0] - nodes[b][0], nodes[a][1] - nodes[b][1]);
    const tan = [], len = [], cell = [], under = [], nb = new Map();
    let run = 0, next = 4 + Math.floor(rnd() * 4);
    for (let i = 0; i < N; i++) {
      const [x, y] = nodes[i], c = G.idx(x, y);
      cell.push(c);
      if (i >= M) {                                                       // plain weave at the crossings, by parity
        const q = strand[i - M], cl = G.cells[c];
        tan.push(q.dir === "v" ? UP : 0); len.push(0.92);
        under.push(!q.end && !!cl && cl.hasV && cl.hasH && (q.dir === "v" ? odd(x, y) : !odd(x, y)));
        continue;
      }
      const a = nodes[Math.max(i - 2, 0)], b = nodes[Math.min(i + 2, M - 1)];
      tan.push(Math.atan2(-(b[1] - a[1]), b[0] - a[0]));
      const dp = i > 0 ? dist(i - 1, i) : dist(i, i + 1), dq = i < M - 1 ? dist(i, i + 1) : dp;
      len.push(0.46 * (dp + dq));                                         // nearly touching its neighbours along the thread
      const u = ++run > next && i > 2 && i < M - 3;                       // long runs over the cloth, single dips under it
      if (u) { run = 0; next = 4 + Math.floor(rnd() * 4); }
      under.push(u);
      for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {  // neighbours the thread drags with it
        const d2 = dx * dx + dy * dy, cn = G.idx(x + dx, y + dy); if (!d2 || d2 > 5 || cn < 0) continue;
        if (!nb.has(cn)) nb.set(cn, []); nb.get(cn).push(i, Math.exp(-d2 / 1.6));
      }
    }
    G.thread = { nodes, M, N, tan, len, cell, under, nb, strand, ic: ic < 0 ? M >> 1 : ic };
  }

  // head and tail run a few nodes past the ends of the thread, so the soft ramps at both ends of the scarlet are complete
  function threadState(t) {
    if (t < T.needle0) return null;
    const { M, ic } = G.thread, H1 = M + 2, dt = t - T.draw0;
    if (dt <= 0) return { head: -1 + SEW((t - T.needle0) / T.weave) * (H1 + 1), tail: -Infinity, front: -Infinity };
    const e = ease(dt / T.reel);
    return { head: H1 - e * (H1 - ic), tail: -4 + e * (ic + 4), front: 22 * RUN(dt / T.run) };
  }
  function weight(th, i, t) {
    const TH = G.thread;
    if (i < TH.M) return Math.min(s01((th.head - i + 1) / 4), s01((i - th.tail) / 4));
    const q = TH.strand[i - TH.M];
    if (q.g === "main") return s01((th.front - q.d + 1) / 3);
    const s = G.F.subs[q.g];                                              // a small cross: out from its own crossing as it locks in
    return s01(((t - T.subs - s.sd / T.ring) * 7 - q.d + 1) / 2.5);
  }
  function figP(cl, k, t, th) {                                // k: 0 = the cell's first stroke, 1 = its crossing stroke
    if (cl.sub) return prog(t, T.subs + cl.sub.sd / T.ring + 0.35 * cl.u, 0.8);
    return th ? ease((th.front - (k === 0 && cl.hasV ? cl.kV : cl.kH)) / 5) : 0;
  }

  function drawHero(t, tau, tc) {
    const P = PAL[hero.dataset.theme === "dark" ? "dark" : "light"], { ctx, cell, fx, fy, cells } = G, TH = G.thread, X = v => fx + v * cell, Y = v => fy + v * cell;
    ctx.fillStyle = P.bg; ctx.fillRect(0, 0, G.W, G.H);
    const th = threadState(t), lines = new Path2D(), red = [], seg = segTo(lines, cell);
    const lw = cell * 0.13, ring = (t - T.subs) * T.ring;
    const rip = t > T.subs ? 0.8 * s01(ring / 6) * (1 - smooth(22, 40, ring)) : 0;
    // which scarlet lies on each cell now: the sewn thread (m) or a cross's own strands (v, h); and the needle, which
    // glides between nodes and fades in and out
    const on = new Map(); let nd = null;
    if (th) {
      const take = (i, key) => { const w = weight(th, i, t), c = TH.cell[i]; if (w <= 0 || c < 0) return;
        if (!on.has(c)) on.set(c, {}); const o = on.get(c); if (!o[key] || w >= o[key].w) o[key] = { i, w }; };
      for (let i = Math.max(0, Math.floor(th.tail)); i <= Math.min(TH.M - 1, Math.floor(th.head) + 1); i++) take(i, "m");
      for (let i = TH.M; i < TH.N; i++) take(i, TH.strand[i - TH.M].dir);
      const al = s01((t - T.needle0) / 0.3) * (1 - s01((t - T.needle0 - T.weave + 0.3) / 0.3));
      if (al > 0) {
        const h = clamp(th.head + 2, 0, TH.M - 1.001), k = Math.floor(h), f = h - k, A = TH.nodes[k], B = TH.nodes[k + 1];
        nd = { x: A[0] + (B[0] - A[0]) * f, y: A[1] + (B[1] - A[1]) * f, a: lerpA(TH.tan[k], TH.tan[k + 1], f), al };
      }
    }
    for (let ci = 0; ci < cells.length; ci++) {
      const cl = cells[ci], cx = X(cl.x), cy = Y(cl.y), wob = 0.3 * Math.sin(2 * PI * tau + cl.noise * 5);
      // order: as the ripple leaves the crossing, each loose stroke behind it turns to the ground's own flow and stays
      const ordr = t > T.subs ? smooth(0, 8, (t - T.subs) / (T.end + 0.6 - T.subs) * (G.dcMax + 8) - cl.dc) : 0, g = lerpA(cl.noise + wob, cl.ord + 0.25 * wob, ordr);
      // every pull on the stroke, blended as axes (angle doubled) so the stroke never jumps from one pull to another
      let pull = 0, sum = 0, vx = 0, vy = 0, room = 1;
      const lean = (b, a) => { if (b < 1e-4) return; if (b > pull) pull = b; sum += b; vx += b * Math.cos(2 * a); vy += b * Math.sin(2 * a); };
      if (tc >= 0) { const q = cl.dc / G.dcMax; lean(0.92 * prog(tc, 1.4 * q, 0.9) * (1 - prog(tc, 3.0 + 1.2 * q, 0.9)), cl.radial); }  // conversi
      if (rip > 0 && cl.group === null) lean(rip * Math.exp(-(((cl.dc - ring) / 3.2) ** 2)), cl.radial);
      if (th) {
        const L = TH.nb.get(ci);
        if (L) for (let m = 0; m < L.length; m += 2) { const w = weight(th, L[m], t); if (w > 0) lean(0.7 * w * L[m + 1], TH.tan[L[m]]); }
        if (nd) { const d2 = (cl.x - nd.x) ** 2 + (cl.y - nd.y) ** 2;
          lean(0.6 * nd.al * Math.exp(-d2 / 2.25), nd.a); room = 1 - nd.al * (1 - smooth(0.15, 1, Math.sqrt(d2))); }   // strokes part for the needle
      }
      const pullA = sum ? Math.atan2(vy, vx) / 2 : 0;
      if (sum) pull *= Math.hypot(vx, vy) / sum;
      // this cell's strokes [angle, length, direction]; the first is the one the sewn thread takes over
      const st = [];
      if (cl.group === null) st.push([lerpA(g, pullA, pull), 0.62 * room, "g"]);
      else (cl.hasV && cl.hasH ? [UP, 0] : cl.hasV ? [UP] : [0]).forEach((tgt, k) => {
        const p = figP(cl, k, t, th), dir = tgt === UP ? "v" : "h";
        if (k === 0) st.push([lerpA(lerpA(g, pullA, pull), tgt, p), (0.62 + 0.28 * p) * room, dir]);
        else if (p > 0) st.push([tgt, 0.9 * p, dir]);
      });
      const o = on.get(ci);
      if (o && (o.v || o.h)) {                                 // a cross's own scarlet takes the stroke of its direction
        // where the sewn thread still lies, the strand nearest its direction takes it over, so the scarlet never blinks
        const mk = !o.m ? null : o.v && o.h ? (Math.abs(Math.sin(TH.tan[o.m.i])) > 0.7 ? "v" : "h") : o.v ? "v" : "h";
        for (const key of ["v", "h"]) { const e = o[key]; if (!e) continue;
          const j = st.findIndex(q => q[2] === key), s0 = j >= 0 ? st[j] : null;
          const w = key === mk ? Math.max(e.w, o.m.w) : e.w, a1 = key === mk ? lerpA(TH.tan[o.m.i], TH.tan[e.i], s01(2 * e.w)) : TH.tan[e.i];
          // under its crossing thread, the stroke sinks out of sight as both arrive
          const sink = TH.under[e.i] ? s01((Math.min(w, figP(cl, key === "v" ? 1 : 0, t, th)) - 0.2) / 0.5) : 0;
          red.push([cx, cy, s0 ? s0[0] : a1, s0 ? s0[1] : 0.16, a1, TH.len[e.i], w, 1 - sink]);
          if (j >= 0) st.splice(j, 1);
        }
      }
      else if (o && o.m) {
        const { i, w } = o.m, s0 = st[0], a1 = TH.tan[i];
        if (!TH.under[i]) { red.push([cx, cy, s0[0], s0[1], a1, TH.len[i], w, 1]); st.shift(); }
        else st[0] = [lerpA(s0[0], a1 + UP, w), s0[1], s0[2]];   // a cloth stroke crosses over the thread
      }
      for (const q of st) seg(cx, cy, q[0], q[1]);
    }
    ctx.strokeStyle = P.ink; ctx.lineWidth = lw; ctx.lineCap = "butt"; ctx.stroke(lines);
    // the scarlet: the same strokes, recoloured, thickened and laid along the thread, each at its own weight
    for (const [cx, cy, a0, l0, a1, l1, w, k] of red) {
      if (k <= 0) continue;
      const p = new Path2D(); segTo(p, cell)(cx, cy, lerpA(a0, a1, w), (l0 + (l1 - l0) * w) * k);
      ctx.strokeStyle = mix(P.ink, P.sc, w); ctx.lineWidth = lw + (cell * 0.26 - lw) * w; ctx.stroke(p);
    }
    if (nd) {                                                  // the needle: a longer ink stroke leading the thread
      const p = new Path2D(); segTo(p, cell)(X(nd.x), Y(nd.y), nd.a, 1.5);
      ctx.globalAlpha = nd.al; ctx.strokeStyle = P.ink; ctx.lineWidth = lw * 1.7; ctx.lineCap = "round"; ctx.stroke(p); ctx.globalAlpha = 1;
    }
  }

  // sequence time only advances while the hero is on screen, and a slow frame slows the motion rather than skipping it
  function frame(now) {
    if (!G.visible || document.hidden) { G.running = false; G.last = null; return; }
    const dt = G.last === null ? 0 : Math.min((now - G.last) / 1000, 1 / 20); G.last = now;
    G.seq += dt;
    if (G.conv >= 0) { G.conv += dt; if (G.conv > 5.5) G.conv = -1; }
    drawHero(Math.min(G.seq, T.end), drift(G.seq), G.conv);
    requestAnimationFrame(frame);
  }
  function wake() { if (!G.running && G.visible && !document.hidden && !reduce) { G.running = true; G.last = null; requestAnimationFrame(frame); } }

  if (hero && cv) {
    const Q = new URLSearchParams(location.search), still = Q.has("t") ? parseFloat(Q.get("t")) : null;   // ?t= for screenshots
    const render = () => { if (!buildHero()) return;
      if (still !== null) drawHero(Math.min(still, T.end), drift(still), parseFloat(Q.get("tc") || "-1"));
      else if (reduce) drawHero(T.end, 0, -1);
      else drawHero(Math.min(G.seq, T.end), drift(G.seq), G.conv); };
    render();
    new ResizeObserver(render).observe(hero);
    if (still === null && !reduce) {
      new IntersectionObserver(es => { G.visible = es.some(e => e.isIntersecting); wake(); }, { threshold: 0.15 }).observe(hero);
      document.addEventListener("visibilitychange", wake);
      hero.addEventListener("click", e => {                    // conversi: the whole field turns toward the crossing
        if (e.target.closest("a, button")) return;
        if (G.seq < T.end) G.seq = T.end;                      // finish the cross first
        G.conv = 0; wake();
      });
    }
  }
  return { renderAt: (t, tc = -1) => drawHero(Math.min(t, T.end), drift(t), tc),
           replay: () => { G.seq = 0; G.conv = -1; if (reduce) drawHero(T.end, 0, -1); else { drawHero(0, 0, -1); wake(); } } };
  }

  // the homepage's field, and every paper's own: [data-sew] holds a canvas.sew-field and is sewn from its data-n
  const heroCv = document.getElementById("hero-field");
  if (heroCv) { const f = Field(heroCv, heroCv.closest(".hero"), heroCv.closest(".hero").dataset.n); window.renderHeroAt = f.renderAt; }
  window.sewn = [...document.querySelectorAll("[data-sew]")].map(el => {
    const f = Field(el.querySelector("canvas"), el, el.dataset.n); el.field = f; return f; });

  // ---------- paper fields: the same cross on every paper; the ground is drawn from the paper's number
  function drawPaper(pc) {
    const W = pc.clientWidth, H = pc.clientHeight; if (!W || !H) return;
    const ctx = sizeCanvas(pc, W, H), P = PAL.light, n = pc.dataset.n || "0";
    const seed = seedOf(n), rnd = mulberry(seed * 7919 + 13);
    const small = W < 80, cols = small ? 9 : 13, cell = W / cols, rows = Math.max(9, Math.floor(H / cell)), oy = (H - rows * cell) / 2;
    const c0 = (cols - 1) / 2, r0 = Math.floor((rows - 1) / 2), current = pc.hasAttribute("data-current");
    const av = small ? 4 : 6, ah = small ? 3 : 5;                    // the arms; smaller fields use fewer, larger cells
    const lw = small ? Math.max(1.1, cell * 0.22) : Math.max(0.9, cell * 0.15), lines = new Path2D(), red = new Path2D(), seg = segTo(lines, cell), segR = segTo(red, cell);
    ctx.fillStyle = P.bg; ctx.fillRect(0, 0, W, H);
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const x = c - c0, y = r - r0, a = rnd() * PI, cx = (c + 0.5) * cell, cy = oy + (r + 0.5) * cell;
      const v = Math.abs(x) <= 1 && Math.abs(y) <= av, h = Math.abs(y) <= 1 && Math.abs(x) <= ah;
      if (!v && !h) { seg(cx, cy, a, 0.62); continue; }
      const cross = v && h;                                    // the scarlet goes under its crossing thread by parity
      if (v) { if (current && x === 0) { if (!(cross && odd(x, y))) segR(cx, cy, UP, 0.92); } else seg(cx, cy, UP, 0.9); }
      if (h) { if (current && y === 0) { if (!(cross && !odd(x, y))) segR(cx, cy, 0, 0.92); } else seg(cx, cy, 0, 0.9); }
    }
    ctx.lineCap = "butt"; ctx.strokeStyle = P.ink; ctx.lineWidth = lw; ctx.stroke(lines);
    if (current) { ctx.strokeStyle = P.sc; ctx.lineWidth = Math.max(1.4, cell * 0.28); ctx.stroke(red); }
  }
  const papers = [...document.querySelectorAll("canvas.paper-field")];
  const drawPapers = () => papers.forEach(drawPaper);
  if (papers.length) { drawPapers(); new ResizeObserver(drawPapers).observe(document.body); }

  // ---------- the mark: three warp and three weft threads, woven, with single-thread crosslets; scarlet middle warp and weft.
  // Below 40 px: the cross alone, in ink only (two scarlet threads that small read as a red plus).
  const MARK = { sub: 5.5, arm: 2 };
  function markSVG(ink, sc, px) {
    const small = px < 40, B = [], add = (x0, x1, y0, y1, dir, main, weave = true) => B.push({ x0, x1, y0, y1, dir, main, weave });
    add(-1, 1, -9, 9, "v", true); add(-9, 9, -1, 1, "h", true);
    if (!small) for (const [x, y] of [[1, -1], [1, 1], [-1, 1], [-1, -1]].map(([p, q]) => [p * MARK.sub, q * MARK.sub])) {
      add(x, x, y - MARK.arm, y + MARK.arm, "v", false, false); add(x - MARK.arm, x + MARK.arm, y, y, "h", false, false); }
    const V = [], Hs = [], g = 0.42, sw = small ? 0.7 : 0.5;
    for (const b of B) {
      if (b.dir === "v") for (let x = b.x0; x <= b.x1; x++) V.push({ x, a: b.y0 - 0.5, b: b.y1 + 0.5, sc: !small && b.main && x === 0, weave: b.weave });
      else for (let y = b.y0; y <= b.y1; y++) Hs.push({ y, a: b.x0 - 0.5, b: b.x1 + 0.5, sc: !small && b.main && y === 0, weave: b.weave });
    }
    const cut = (a, b, breaks) => { const out = []; let s = a;
      breaks.sort((p, q) => p - q).forEach(k => { out.push([s, k - g]); s = k + g; }); out.push([s, b]); return out.filter(([p, q]) => q > p); };
    const oddR = (x, y) => ((Math.round(x + y) % 2) + 2) % 2 === 1;
    let d = "", ds = "";
    for (const v of V) {
      const br = v.weave ? Hs.filter(h => h.weave && h.a <= v.x && v.x <= h.b && v.a <= h.y && h.y <= v.b && oddR(v.x, h.y)).map(h => h.y) : [];
      cut(v.a, v.b, br).forEach(([p, q]) => { const s = `M${v.x} ${p}V${q}`; v.sc ? ds += s : d += s; });
    }
    for (const h of Hs) {
      const br = h.weave ? V.filter(v => v.weave && v.a <= h.y && h.y <= v.b && h.a <= v.x && v.x <= h.b && !oddR(v.x, h.y)).map(v => v.x) : [];
      cut(h.a, h.b, br).forEach(([p, q]) => { const s = `M${p} ${h.y}H${q}`; h.sc ? ds += s : d += s; });
    }
    return `<svg width="${px}" height="${px}" viewBox="-9.5 -9.5 19 19" fill="none" stroke-linecap="butt" aria-hidden="true" focusable="false">` +
           `<path d="${d}" style="stroke:${ink}" stroke-width="${sw}"/><path d="${ds}" style="stroke:${sc}" stroke-width="${sw}"/></svg>`;
  }
  document.querySelectorAll("span.mark[data-size]").forEach(el => {
    const P = PAL[el.dataset.theme === "dark" ? "dark" : "light"], px = parseInt(el.dataset.size || "28", 10);
    el.innerHTML = markSVG(P.ink, P.sc, px);
    el.style.display = "inline-block"; el.style.width = el.style.height = px + "px"; el.style.lineHeight = "0"; el.style.flexShrink = "0";
  });
})();
