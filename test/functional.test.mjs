// Functional tests for the Shift Puzzle — drives the BUILT page in headless
// Chrome over the DevTools Protocol and asserts real gameplay behaviour that the
// engine unit tests can't reach: solving levels to a win, the candy move-economy
// and (repeatable) undo, out-of-moves recovery, and a smoke pass over every mode.
//
// Run with the preview server already serving the build:
//   npm run build && npm run preview &   # then:
//   node test/functional.test.mjs http://localhost:4321
// or just `node test/functional.test.mjs` and it will build+preview itself.

import { spawn, execFileSync } from 'child_process';
import { setTimeout as delay } from 'timers/promises';

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DBG_PORT = 9211;
const PROFILE = '/tmp/shiftpuzzle-test-profile';

let baseUrl = process.argv[2];
let previewProc = null;

async function ensureServer() {
  if (baseUrl) return baseUrl;                       // caller supplied a URL
  execFileSync('npm', ['run', 'build'], { cwd: process.cwd(), stdio: 'ignore' });
  previewProc = spawn('npm', ['run', 'preview'], { cwd: process.cwd(), stdio: ['ignore', 'pipe', 'ignore'] });
  for (let i = 0; i < 80; i++) {
    const line = await readLine(previewProc.stdout);
    const m = line && line.match(/localhost:(\d+)/);
    if (m) { baseUrl = `http://localhost:${m[1]}`; break; }
  }
  if (!baseUrl) throw new Error('preview server did not start');
  await delay(800);
  return baseUrl;
}
function readLine(stream) {
  return new Promise(res => { const onData = d => { stream.off('data', onData); res(d.toString()); }; stream.on('data', onData); setTimeout(() => { stream.off('data', onData); res(''); }, 1500); });
}

async function devtoolsWs() {
  for (let i = 0; i < 60; i++) {
    try {
      const list = JSON.parse(execFileSync('curl', ['-s', `http://localhost:${DBG_PORT}/json`]).toString());
      const pg = list.find(t => t.type === 'page' && t.url.includes('shift-puzzle'));
      if (pg && pg.webSocketDebuggerUrl) return pg.webSocketDebuggerUrl;
    } catch (e) { /* not up yet */ }
    await delay(150);
  }
  throw new Error('no devtools target');
}

function makeClient(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0; const pending = new Map();
  const ready = new Promise(r => ws.addEventListener('open', () => r()));
  ws.addEventListener('message', ev => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const cmd = (method, params) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expr) => {
    const r = await cmd('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.result && r.result.exceptionDetails) throw new Error('page exception: ' + JSON.stringify(r.result.exceptionDetails));
    return r.result.result.value;
  };
  return { cmd, ev, ready, close: () => ws.close() };
}

// ---- harness ----
let passed = 0, failed = 0; const fails = [];
function check(name, cond, detail) { if (cond) passed++; else { failed++; fails.push(name + (detail ? ' — ' + detail : '')); } }

// In-page helpers, injected once: a BFS solver for windowed solve levels and a
// settle() that waits out candy animations. Defined as a string the page runs.
const HELPERS = `
window.__t = {
  sleep: ms => new Promise(r => setTimeout(r, ms)),
  settle: async () => { for (let i = 0; i < 400; i++) { if (!(window.candyAnimating)) return; await new Promise(r => setTimeout(r, 10)); } },
  waitGen: async () => { for (let i = 0; i < 300; i++) { if (!generating) return true; await new Promise(r => setTimeout(r, 20)); } return false; },
  solveWindow: () => {
    const NAMES = ['U','D','L','R','CW','CCW'];
    const apply = (s, m) => applyMove(s, m); const key = s => Array.from(s).join();
    const idx = winIdx, g = Array.from(goal);
    const matches = b => { for (const [bi, ti] of idx) if (b[bi] !== g[ti]) return false; return true; };
    const sa = state.slice(); if (matches(sa)) return [];
    let f = [{ s: sa, p: [] }]; const seen = new Set([key(sa)]); let d = 0;
    while (f.length && d <= optimal + 1) { d++; const nf = [];
      for (const nd of f) for (const m of NAMES) { const ns = apply(nd.s, m); const k = key(ns); const np = nd.p.concat(m);
        if (matches(ns)) return np; if (!seen.has(k)) { seen.add(k); nf.push({ s: ns, p: np }); } }
      f = nf; }
    return null;
  }
};`;

async function run() {
  await ensureServer();
  const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    `--remote-debugging-port=${DBG_PORT}`, `--user-data-dir=${PROFILE}`, `${baseUrl}/shift-puzzle/`], { stdio: 'ignore' });
  let cl;
  try {
    cl = makeClient(await devtoolsWs());
    await cl.ready;
    await cl.ev('1+1');
    await delay(600);
    await cl.ev(HELPERS);

    // --- A. every solve level (L1..L15) generates and can be solved to a win ---
    for (let L = 1; L <= 15; L++) {
      const res = await cl.ev(`(async () => {
        els.difficulty.value = 'L${L}'; applyDifficulty('L${L}', false);
        if (!(await __t.waitGen())) return { ok:false, why:'timeout' };
        const path = __t.solveWindow();
        if (!path) return { ok:false, why:'no solution found' };
        for (const m of path) doMove(m);
        return { ok: solved && document.getElementById('win').classList.contains('show'), len: path.length, optimal };
      })()`);
      check(`L${L} solves to win`, res && res.ok, res && (res.why || `len ${res.len} vs optimal ${res.optimal}`));
    }

    // --- B. candy smoke: every candy mode loads, accepts a move, no exception ---
    for (const C of ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9']) {
      const res = await cl.ev(`(async () => {
        els.difficulty.value = '${C}'; applyDifficulty('${C}', false); await __t.sleep(60);
        if (!candy) return { ok:false, why:'not candy' };
        const full = state.every(v => v !== 0);
        doMove('CW'); await __t.settle();
        return { ok: full, score, moves: candyMoves };
      })()`);
      check(`${C} loads & plays`, res && res.ok, res && res.why);
    }

    // --- C. candy undo is a REPEATABLE stack: several non-clearing moves can each
    //        be undone in turn, each refunding a move and re-lighting the undo. ---
    {
      const res = await cl.ev(`(async () => {
        const INV = { U:'D', D:'U', L:'R', R:'L', CW:'CCW', CCW:'CW' };
        els.difficulty.value = 'C8'; applyDifficulty('C8', false); await __t.sleep(60);
        // make a sequence of NON-clearing moves, recording board+moves before each
        const log = [];
        let guard = 0;
        while (log.length < 3 && guard++ < 40) {
          const before = { board: Array.from(state), moves: candyMoves, last: lastMove };
          const scoreBefore = score;
          doMove('CW'); await __t.settle();
          if (score === scoreBefore && !candyLost) log.push(before);
          else { log.length = 0; } // a clear wiped history; restart the sequence
        }
        if (log.length < 3) return { ok:false, why:'could not get 3 non-clearing moves' };
        // now undo three times; each must restore the prior snapshot and re-light undo
        let okCount = 0;
        for (let k = log.length - 1; k >= 0; k--) {
          const undoBtn = candyUndoMoveName ? candyUndoMoveName() : (lastMove ? INV[lastMove] : null);
          if (!undoBtn) break;
          doMove(undoBtn); await __t.settle();
          const want = log[k];
          if (Array.from(state).join() === want.board.join() && candyMoves === want.moves) okCount++;
        }
        return { ok: okCount === 3, okCount };
      })()`);
      check('candy undo is a repeatable stack', res && res.ok, res && `restored ${res.okCount}/3 (${res.why || ''})`);
    }

    // --- D. out of moves: the undo button stays clickable and unwinds the loss ---
    {
      const res = await cl.ev(`(async () => {
        const INV = { U:'D', D:'U', L:'R', R:'L', CW:'CCW', CCW:'CW' };
        els.difficulty.value = 'C8'; applyDifficulty('C8', false); await __t.sleep(60);
        let guard = 0;
        while (!candyLost && guard++ < 250) { doMove('CW'); await __t.settle(); }
        if (!candyLost) return { ok:false, why:'never ran out of moves' };
        // the undo-hint button must NOT be inert (no 'spent', frame may be 'locked'
        // but the CSS keeps undo-hint clickable). Verify class state + that a tap works.
        const undoName = candyUndoMoveName ? candyUndoMoveName() : (lastMove ? INV[lastMove] : null);
        if (!undoName) return { ok:false, why:'no undo available when lost' };
        const btn = [...document.querySelectorAll('.frame button[data-move]')].find(b => b.dataset.move === undoName);
        const inert = btn.classList.contains('spent');
        const movesBefore = candyMoves;
        doMove(undoName); await __t.settle();
        return { ok: !inert && !candyLost && candyMoves > movesBefore, inert, lostAfter: candyLost, moves: candyMoves };
      })()`);
      check('out-of-moves undo recovers', res && res.ok, res && `inert=${res.inert} lostAfter=${res.lostAfter} moves=${res.moves} ${res.why || ''}`);
    }

    // --- E. shape targets are always feasible (colour count >= shape size) ---
    for (const C of ['C6', 'C7', 'C8']) {
      const res = await cl.ev(`(async () => {
        els.difficulty.value = '${C}'; applyDifficulty('${C}', false); await __t.sleep(60);
        let bad = 0;
        for (let i = 0; i < 60; i++) {
          document.getElementById('resetBtn').click();
          const cnt = {}; for (const v of state) if (v) { const c = decC(v); cnt[c] = (cnt[c]||0)+1; }
          for (const t of [candyTarget, candyNextTarget]) if ((cnt[t.C]||0) < t.shape.length) bad++;
        }
        return { ok: bad === 0, bad };
      })()`);
      check(`${C} targets always feasible`, res && res.ok, res && `${res.bad} infeasible`);
    }

  } finally {
    if (cl) cl.close();
    chrome.kill('SIGKILL');
    if (previewProc) previewProc.kill('SIGKILL');
  }

  console.log(`\nfunctional.test.mjs: ${passed} passed, ${failed} failed`);
  if (failed) { console.log('FAILURES:'); for (const f of fails) console.log('  - ' + f); process.exit(1); }
  console.log('ALL FUNCTIONAL TESTS PASSED');
}

run().catch(e => { console.error('HARNESS ERROR:', e.message); if (previewProc) previewProc.kill('SIGKILL'); process.exit(2); });
