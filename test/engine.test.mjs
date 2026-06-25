// Engine unit tests for the Shift Puzzle (public/shift-puzzle/index.html).
//
// The game is now candy SHAPE modes only (S1-S5). These tests extract the pure
// geometry/shape logic from the page's single inline <script> and check the
// invariants the game depends on: move algebra, the turn-on-exit rotation rule,
// the centre spin, shape feasibility (colour-count sufficiency, no edge-wrap),
// and the partial-axis target structure. No browser; run: node test/engine.test.mjs

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const HTML = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'shift-puzzle', 'index.html');
const html = readFileSync(HTML, 'utf8');

// Extract the pure functions: slice the inline <script> from the first geometry
// helper to just before the DOM-touching `els` map, and evaluate in a sandbox.
const script = [...html.matchAll(/<script>\s*([\s\S]*?)<\/script>/g)].map(m => m[1])
  .find(s => s.includes('function buildPerms') && s.includes('function findShape'));
if (!script) { console.error('could not find main script'); process.exit(2); }
const slice = script.slice(script.indexOf('function ringsOf'), script.indexOf('const els = {'));

const makeApi = new Function(`
  let perms = null, edge = null, oriented = false, candyCfg = null;
  ${slice}
  return {
    buildPerms, edgeMask, applyMove, applyPerm, decC, decO, rotCell,
    findShape, randomShape, ensureTarget, makeAxisTarget, ensureDualTargets,
    bothPresent, candyGravity, candySpawn, candyCell,
    setPerms: v => perms = v, setEdge: v => edge = v, setOriented: v => oriented = v,
    setCfg: v => candyCfg = v, getCfg: () => candyCfg,
  };
`);
const api = makeApi();

let passed = 0, failed = 0; const fails = [];
function check(name, cond, detail) { if (cond) passed++; else { failed++; fails.push(name + (detail ? ' — ' + detail : '')); } }

const NAMES = ['U', 'D', 'L', 'R', 'CW', 'CCW'];
const INV = { U: 'D', D: 'U', L: 'R', R: 'L', CW: 'CCW', CCW: 'CW' };
const key = s => String.fromCharCode.apply(null, s);
const eq = (a, b) => { if (a.length !== b.length) return false; for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false; return true; };
const enc = (c, o) => 1 + c * 4 + (((o % 4) + 4) % 4);
const isCorner = (n, idx) => { const r = (idx / n) | 0, c = idx % n, k = Math.min(r, c, n - 1 - r, n - 1 - c), lo = k, hi = n - 1 - k; return (r === lo || r === hi) && (c === lo || c === hi); };

api.setCfg({ candy: true, size: 3, colors: 3, match: 'shape', shapeMin: 2, shapeMax: 3 });

// Bind the module-level perms/edge/oriented the 2-arg applyMove reads.
function bind(n, oriented) { api.setPerms(api.buildPerms(n)); api.setEdge(api.edgeMask(n)); api.setOriented(oriented); }

// 1. Move algebra
for (const n of [3, 4, 5]) {
  bind(n, true);
  const distinct = new Uint8Array(n * n);
  for (let i = 0; i < n * n; i++) distinct[i] = enc(i % 6, i % 4);
  for (const m of NAMES) {
    const back = api.applyMove(api.applyMove(distinct, m), INV[m]);
    check(`inverse n=${n} ${m}`, eq(back, distinct));
  }
  { let s = distinct, steps = 0; do { s = api.applyMove(s, 'CW'); steps++; } while (!eq(s, distinct) && steps < 5000); check(`CW returns to identity n=${n}`, eq(s, distinct)); }
  // plain (oriented=false): no orientation drift
  bind(n, false);
  const upright = new Uint8Array(n * n); for (let i = 0; i < n * n; i++) upright[i] = enc(i % 6, 0);
  for (const m of NAMES) { const a = api.applyMove(upright, m); let drift = false; for (let i = 0; i < n * n; i++) if (a[i] !== 0 && api.decO(a[i]) !== 0) drift = true; check(`plain no-drift n=${n} ${m}`, !drift); }
}

// 2. Rotation = turn-on-exit; centre spins
for (const n of [3, 4, 5]) {
  bind(n, true);
  const P = api.buildPerms(n);
  const base = new Uint8Array(n * n); for (let i = 0; i < n * n; i++) base[i] = enc(i % 6, i % 4);
  const after = api.applyMove(base, 'CW');
  let wrong = 0;
  for (let i = 0; i < n * n; i++) { const src = P.CW[i]; if (api.decO(after[i]) !== api.decO(base[src]) && !isCorner(n, src) && src !== i) wrong++; }
  check(`turn-on-exit n=${n}`, wrong === 0, `${wrong} turned without leaving a corner`);
  if (n % 2 === 1) {
    const c = ((n * n - 1) / 2) | 0; const probe = new Uint8Array(n * n); probe[c] = enc(0, 0);
    check(`centre spins CW n=${n}`, api.decO(api.applyMove(probe, 'CW')[c]) === 1);
    check(`centre spins CCW n=${n}`, api.decO(api.applyMove(probe, 'CCW')[c]) === 3);
  }
}

// 3. Shape match: no edge-wrap; colour-count = feasibility
{
  const n = 3, P = api.buildPerms(n), edge = api.edgeMask(n);
  api.setPerms(P); api.setEdge(edge);
  api.setOriented(true);
  const b = new Uint8Array(9);
  b[0] = enc(0, 0); b[1] = enc(1, 0); b[2] = enc(0, 0); for (let i = 3; i < 9; i++) b[i] = enc(2, 0);
  check('no edge-wrap match', !api.findShape(b, { shape: [[0, 0], [0, 1]], C: 0 }, n));
  const b2 = new Uint8Array(9); b2[0] = enc(0, 0); b2[1] = enc(0, 0); for (let i = 2; i < 9; i++) b2[i] = enc(2, 0);
  check('adjacent pair matches', !!api.findShape(b2, { shape: [[0, 0], [0, 1]], C: 0 }, n));
  function reachable(board, t) {
    if (api.findShape(board, t, n)) return true;
    let front = [board]; const seen = new Set([key(board)]);
    while (front.length) { const nf = []; for (const st of front) for (const m of NAMES) { const ns = api.applyPerm(st, P[m], n); const k = key(ns); if (seen.has(k)) continue; if (api.findShape(ns, t, n)) return true; seen.add(k); nf.push(ns); } front = nf; }
    return false;
  }
  let counter = 0, tested = 0;
  for (let t = 0; t < 600; t++) {
    const board = new Uint8Array(9); for (let i = 0; i < 9; i++) board[i] = enc((Math.random() * 3) | 0, 0);
    const cnt = {}; for (const v of board) cnt[api.decC(v)] = (cnt[api.decC(v)] || 0) + 1;
    const C = (Math.random() * 3) | 0, sz = 2 + ((Math.random() * 2) | 0);
    if ((cnt[C] || 0) < sz) continue;
    const shape = api.randomShape(sz, n); if (shape.length !== sz) continue;
    tested++; if (!reachable(board, { shape, C })) counter++;
  }
  check('colour-count => reachable', counter === 0, `${counter}/${tested} unreachable`);
}

// 4. ensureTarget always board-feasible, every mode
for (const cfg of [
  { match: 'shape', shapeMin: 2, shapeMax: 3 },
  { match: 'shape', shapeMin: 3, shapeMax: 4 },
  { match: 'shapeA', shapeMin: 3, shapeMax: 4, partialAxis: false },
  { match: 'shapeA', shapeMin: 3, shapeMax: 4, partialAxis: true },
]) {
  const n = 3; api.setCfg({ candy: true, size: n, colors: 3, ...cfg });
  api.setPerms(api.buildPerms(n)); api.setEdge(api.edgeMask(n));
  let bad = 0, total = 0;
  for (let t = 0; t < 300; t++) {
    const b = new Uint8Array(n * n); for (let i = 0; i < n * n; i++) b[i] = api.candySpawn();
    const tg = api.ensureTarget(b, n, -1);
    let cnt = 0; for (const v of b) if (v !== 0 && api.decC(v) === tg.C) cnt++;
    total++; if (cnt < tg.shape.length) bad++;
  }
  check(`ensureTarget feasible [${cfg.match}${cfg.partialAxis ? ' partial' : ''}]`, bad === 0, `${bad}/${total} infeasible`);
}

// 5. Partial-axis structure
{
  const n = 3;
  api.setCfg({ candy: true, size: n, colors: 3, match: 'shapeA', shapeMin: 3, shapeMax: 4, partialAxis: true });
  api.setPerms(api.buildPerms(n)); api.setEdge(api.edgeMask(n));
  let mixed = 0, total = 0, hasAxes = 0;
  for (let t = 0; t < 200; t++) {
    const b = new Uint8Array(n * n); for (let i = 0; i < n * n; i++) b[i] = api.candySpawn();
    const tg = api.ensureTarget(b, n, -1); total++;
    if (tg.axes) { hasAxes++; const set = tg.axes.filter(a => a != null).length, nul = tg.axes.filter(a => a == null).length; if (set > 0 && nul > 0) mixed++; }
  }
  check('partial-axis targets carry per-cell axes', hasAxes === total, `${hasAxes}/${total}`);
  check('partial-axis targets are a real mix', mixed === total, `${mixed}/${total} mixed`);
  api.setCfg({ candy: true, size: n, colors: 3, match: 'shapeA', shapeMin: 3, shapeMax: 4, partialAxis: false });
  let fullOk = true;
  for (let t = 0; t < 50; t++) { const b = new Uint8Array(n * n); for (let i = 0; i < n * n; i++) b[i] = api.candySpawn(); const tg = api.ensureTarget(b, n, -1); if (tg.axes || tg.axis == null) fullOk = false; }
  check('full-axis targets use a single axis', fullOk);
}

// 6. Dual targets distinct + feasible
{
  const n = 3; api.setCfg({ candy: true, size: n, colors: 3, match: 'dual', shapeMin: 2, shapeMax: 3 });
  api.setPerms(api.buildPerms(n)); api.setEdge(api.edgeMask(n));
  let bad = 0, total = 0;
  for (let t = 0; t < 120; t++) {
    const b = new Uint8Array(n * n); for (let i = 0; i < n * n; i++) b[i] = api.candySpawn();
    const [a, bb] = api.ensureDualTargets(b, n); total++;
    const cnt = {}; for (const v of b) if (v !== 0) cnt[api.decC(v)] = (cnt[api.decC(v)] || 0) + 1;
    if (a.C === bb.C) bad++;
    else if ((cnt[a.C] || 0) < a.shape.length || (cnt[bb.C] || 0) < bb.shape.length) bad++;
  }
  check('dual targets: distinct colours, both feasible', bad === 0, `${bad}/${total} bad`);
}

console.log(`\nengine.test.mjs: ${passed} passed, ${failed} failed`);
if (failed) { console.log('FAILURES:'); for (const f of fails) console.log('  - ' + f); process.exit(1); }
console.log('ALL ENGINE TESTS PASSED');
