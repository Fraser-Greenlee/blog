// Engine unit tests for the Shift Puzzle (public/shift-puzzle/index.html).
//
// These extract the *pure* logic from the page's two inline scripts (the Web
// Worker generator and the main-thread geometry) and check the invariants the
// whole game depends on — move algebra, exact-optimal generation, orientation
// rules, and shape feasibility. No browser needed; run with:  node test/engine.test.mjs
//
// Functional/UI behaviour (undo stack, animations, lose state) lives in
// test/functional.test.mjs, which drives the built page in headless Chrome.

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const HTML = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'shift-puzzle', 'index.html');
const html = readFileSync(HTML, 'utf8');

// ---- extract the worker script and expose its functions ----
const workerSrc = html.match(/<script id="workerSrc"[^>]*>([\s\S]*?)<\/script>/)[1];
const W = (new Function(`${workerSrc.replace('onmessage = function', 'var _om = function')}
  return { buildPerms, edgeMask, applyMove, decC, decO, biBFS, generate, ringsOf, MOVES };`))();

// ---- extract the main-thread geometry (to check worker/main parity) ----
const mains = [...html.matchAll(/<script>\s*([\s\S]*?)<\/script>/g)].map(m => m[1]);
const main = mains.find(s => s.includes('function applyMove') && s.includes('edgeMask') && s.includes('rotCell'));
const geom = main.substring(main.indexOf('// Cell encoding mirrors'), main.indexOf('// The board is solved'));
// main applyMove reads module-scoped perms/edge/oriented; wrap so we can bind them.
const mainApplyFactory = new Function('perms', 'edge', 'oriented', `${geom}\n return (st, move) => applyMove(st, move);`);

// ---- tiny test harness ----
let passed = 0, failed = 0;
const fails = [];
function check(name, cond, detail) {
  if (cond) { passed++; }
  else { failed++; fails.push(name + (detail ? ' — ' + detail : '')); }
}
function section(s) { /* grouping marker, printed in summary on failure */ }

const NAMES = ['U', 'D', 'L', 'R', 'CW', 'CCW'];
const INV = { U: 'D', D: 'U', L: 'R', R: 'L', CW: 'CCW', CCW: 'CW' };
const key = s => String.fromCharCode.apply(null, s);
const eq = (a, b) => { if (a.length !== b.length) return false; for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false; return true; };
const enc = (c, o) => 1 + c * 4 + (((o % 4) + 4) % 4);
const isCorner = (n, idx) => { const r = (idx / n) | 0, c = idx % n, k = Math.min(r, c, n - 1 - r, n - 1 - c), lo = k, hi = n - 1 - k; return (r === lo || r === hi) && (c === lo || c === hi); };

// =====================================================================
// 1. Move algebra: parity, inverses, full-lap identity
// =====================================================================
for (const n of [3, 4, 5, 6]) {
  const P = W.buildPerms(n), edge = W.edgeMask(n);
  const mainApply = mainApplyFactory(P, edge, true);
  const distinct = new Uint8Array(n * n);
  for (let i = 0; i < n * n; i++) distinct[i] = enc(i % 6, i % 4);

  // worker applyMove === main applyMove (oriented), for every move
  for (const m of NAMES) {
    check(`parity n=${n} ${m}`, eq(W.applyMove(distinct, m, P, edge, true), mainApply(distinct, m)));
  }
  // each move composed with its inverse is identity
  for (const m of NAMES) {
    const back = W.applyMove(W.applyMove(distinct, m, P, edge, true), INV[m], P, edge, true);
    check(`inverse n=${n} ${m}`, eq(back, distinct));
  }
  // Repeating CW its full order returns to identity (positions AND orientation).
  // The order is lcm(ring lengths) * (4 / gcd) — simplest to just find it: apply
  // CW until we return to start (bounded), and confirm we do within the bound.
  // This catches any orientation that fails to return to a multiple of 360.
  {
    let s = distinct, steps = 0; const maxSteps = 5000;
    do { s = W.applyMove(s, 'CW', P, edge, true); steps++; } while (!eq(s, distinct) && steps < maxSteps);
    check(`CW returns to identity n=${n}`, eq(s, distinct), `did not return within ${maxSteps} steps`);
  }

  // plain (non-oriented) moves never change orientation bits
  const upright = new Uint8Array(n * n); for (let i = 0; i < n * n; i++) upright[i] = enc(i % 6, 0);
  for (const m of NAMES) {
    const a = W.applyMove(upright, m, P, edge, false);
    let drift = false; for (let i = 0; i < n * n; i++) if (a[i] !== 0 && W.decO(a[i]) !== 0) drift = true;
    check(`plain no-orient-drift n=${n} ${m}`, !drift);
  }
}

// =====================================================================
// 2. Rotation rule: a piece turns ONLY as it LEAVES a corner (not entering)
//    and the centre of an odd grid spins in place.
// =====================================================================
for (const n of [3, 4, 5]) {
  const P = W.buildPerms(n), edge = W.edgeMask(n);
  const base = new Uint8Array(n * n); for (let i = 0; i < n * n; i++) base[i] = enc(i % 6, i % 4);
  const after = W.applyMove(base, 'CW', P, edge, true);
  // every piece that changed orientation must have come FROM a corner source
  // (or be the centre, which maps to itself); none should turn merely by arriving.
  let wrong = 0;
  for (let i = 0; i < n * n; i++) {
    const src = P.CW[i];
    const turned = W.decO(after[i]) !== W.decO(base[src]);
    if (turned && !isCorner(n, src) && src !== i) wrong++;
  }
  check(`turn-on-exit n=${n}`, wrong === 0, `${wrong} pieces turned without leaving a corner`);

  if (n % 2 === 1) {
    const c = ((n * n - 1) / 2) | 0;
    const probe = new Uint8Array(n * n); probe[c] = enc(0, 0); // up
    const cw = W.applyMove(probe, 'CW', P, edge, true);
    const ccw = W.applyMove(probe, 'CCW', P, edge, true);
    check(`centre spins CW n=${n}`, W.decO(cw[c]) === 1);   // up -> right
    check(`centre spins CCW n=${n}`, W.decO(ccw[c]) === 3); // up -> left
  }
}

// =====================================================================
// 3. Exact-optimal generation (bidirectional BFS) — solve-mode levels.
//    Independent forward BFS must agree on the minimum, and confirm the
//    target is NOT reachable one move sooner.
// =====================================================================
function fwdMinFull(start, goal, P, edge, oriented, n, cap) {
  // forward BFS to an exact full-board goal; returns min depth or -1
  if (eq(start, goal)) return 0;
  let front = [start]; const seen = new Set([key(start)]); let d = 0, nodes = 0;
  const gk = key(goal);
  while (front.length && d < cap) {
    d++; const nf = [];
    for (const st of front) for (const m of NAMES) {
      const ns = W.applyMove(st, m, P, edge, oriented), k = key(ns);
      if (k === gk) return d;
      if (!seen.has(k)) { seen.add(k); nf.push(ns); if (++nodes > 250000) return -2; }
    }
    front = nf;
  }
  return -1;
}
// generate(n, wd, colors, cells, decoys, oriented, picture, K, floor, A, cap)
for (const [label, n, colors, cells, oriented, K, floor, A] of [
  ['solve 3x3 plain', 3, 2, 3, false, 8, 4, 4],
  ['solve 3x3 oriented', 3, 2, 3, true, 8, 5, 4],
]) {
  const P = W.buildPerms(n), edge = W.edgeMask(n);
  let mism = 0, shortBeat = 0;
  for (let t = 0; t < 12; t++) {
    const r = W.generate(n, n, colors, cells, 0, oriented, false, K, floor, A, 1200000);
    const start = Uint8Array.from(r.start), goal = Uint8Array.from(r.goal);
    const indep = fwdMinFull(start, goal, P, edge, oriented, n, r.min + 1);
    if (indep !== r.min) mism++;
    if (r.min > 1 && fwdMinFull(start, goal, P, edge, oriented, n, r.min - 1) !== -1) shortBeat++;
  }
  check(`${label}: optimum exact`, mism === 0, `${mism}/12 mismatched`);
  check(`${label}: not beatable in min-1`, shortBeat === 0, `${shortBeat}/12 beatable`);
}

// =====================================================================
// 4. Shape feasibility (candy shape modes): a target whose colour has >=
//    shape-size tiles is always reachable on 3x3 — the criterion the game
//    relies on (no capped-BFS false negatives).
// =====================================================================
{
  const n = 3, P = W.buildPerms(n), edge = W.edgeMask(n);
  const decC = W.decC;
  function findShape(b, shape, C) { // no-wrap, colour only
    let mr = 0, mc = 0; for (const [dr, dc] of shape) { if (dr > mr) mr = dr; if (dc > mc) mc = dc; }
    for (let or = 0; or + mr < n; or++) for (let oc = 0; oc + mc < n; oc++) {
      let ok = true; for (const [dr, dc] of shape) { const v = b[(or + dr) * n + (oc + dc)]; if (v === 0 || decC(v) !== C) { ok = false; break; } }
      if (ok) return true;
    }
    return false;
  }
  function reachable(b, shape, C) { // uncapped BFS to shape-present (colour only)
    if (findShape(b, shape, C)) return true;
    let front = [b]; const seen = new Set([key(b)]);
    while (front.length) { const nf = []; for (const st of front) for (const m of ['U', 'D', 'L', 'R', 'CW', 'CCW']) { const ns = W.applyMove(st, m, P, edge, false); const k = key(ns); if (seen.has(k)) continue; if (findShape(ns, shape, C)) return true; seen.add(k); nf.push(ns); } front = nf; }
    return false;
  }
  function randomShape(sz) { // connected-ish blob fitting 3x3
    let cells; do { const s = new Set(['0,0']); let cur = [0, 0]; let g = 0; while (s.size < sz && g++ < 60) { const d = [[0, 1], [0, -1], [1, 0], [-1, 0]][(Math.random() * 4) | 0]; cur = [cur[0] + d[0], cur[1] + d[1]]; s.add(cur[0] + ',' + cur[1]); } const pts = [...s].map(x => x.split(',').map(Number)); const mr = Math.min(...pts.map(p => p[0])), mc = Math.min(...pts.map(p => p[1])); cells = pts.map(([r, c]) => [r - mr, c - mc]); } while (cells.length !== sz || Math.max(...cells.map(p => p[0])) >= n || Math.max(...cells.map(p => p[1])) >= n); return cells; }

  let counter = 0, tested = 0;
  for (let t = 0; t < 800; t++) {
    const b = new Uint8Array(n * n); for (let i = 0; i < n * n; i++) b[i] = enc((Math.random() * 3) | 0, 0);
    const cnt = {}; for (const v of b) cnt[decC(v)] = (cnt[decC(v)] || 0) + 1;
    const C = (Math.random() * 3) | 0, sz = 2 + ((Math.random() * 2) | 0);
    if ((cnt[C] || 0) < sz) continue;
    const shape = randomShape(sz); if (shape.length !== sz) continue;
    tested++;
    if (!reachable(b, shape, C)) counter++;
  }
  check('shape feasibility = colour-count sufficiency', counter === 0, `${counter}/${tested} count-sufficient but unreachable`);
}

// =====================================================================
// 5. Generated boards are non-trivial (start !== goal) and within bounds.
// =====================================================================
{
  const n = 3;
  let bad = 0;
  for (let t = 0; t < 12; t++) {
    const r = W.generate(n, n, 2, 3, 0, false, false, 8, 4, 4, 1200000);
    if (r.min < 1) bad++;
    if (r.start.length !== n * n || r.goal.length !== n * n) bad++;
  }
  check('generated boards non-trivial & sized', bad === 0);
}

// ---- report ----
console.log(`\nengine.test.mjs: ${passed} passed, ${failed} failed`);
if (failed) { console.log('FAILURES:'); for (const f of fails) console.log('  - ' + f); process.exit(1); }
console.log('ALL ENGINE TESTS PASSED');
