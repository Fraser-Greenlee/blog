// Functional tests for the Shift Puzzle — drives the BUILT page in headless
// Chrome (DevTools Protocol) and asserts real gameplay for the candy SHAPE modes
// (S1-S5): each mode loads & plays, targets stay feasible, the repeatable undo
// stack works, out-of-moves undo recovers, dual clears both shapes, and the
// partial-axis variant renders fewer bars than cells.
//
// Run against a preview server you start:
//   npm run build && npm run preview &   # then:
//   node test/functional.test.mjs http://localhost:4321
// or `node test/functional.test.mjs` to build + preview itself.

import { spawn, execFileSync } from 'child_process';
import { setTimeout as delay } from 'timers/promises';

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DBG_PORT = 9212;
const PROFILE = '/tmp/shiftpuzzle-test-profile';

let baseUrl = process.argv[2];
let previewProc = null;

async function ensureServer() {
  if (baseUrl) return baseUrl;
  execFileSync('npm', ['run', 'build'], { cwd: process.cwd(), stdio: 'ignore' });
  previewProc = spawn('npm', ['run', 'preview'], { cwd: process.cwd(), stdio: ['ignore', 'pipe', 'ignore'] });
  for (let i = 0; i < 80; i++) {
    const line = await new Promise(res => { const s = previewProc.stdout; const f = d => { s.off('data', f); res(d.toString()); }; s.on('data', f); setTimeout(() => { s.off('data', f); res(''); }, 1500); });
    const m = line && line.match(/localhost:(\d+)/);
    if (m) { baseUrl = `http://localhost:${m[1]}`; break; }
  }
  if (!baseUrl) throw new Error('preview server did not start');
  await delay(800);
  return baseUrl;
}
async function devtoolsWs() {
  for (let i = 0; i < 60; i++) {
    try { const list = JSON.parse(execFileSync('curl', ['-s', `http://localhost:${DBG_PORT}/json`]).toString());
      const pg = list.find(t => t.type === 'page' && t.url.includes('shift-puzzle'));
      if (pg && pg.webSocketDebuggerUrl) return pg.webSocketDebuggerUrl; } catch (e) {}
    await delay(150);
  }
  throw new Error('no devtools target');
}
function makeClient(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0; const pending = new Map(); const errors = [];
  const ready = new Promise(r => ws.addEventListener('open', () => r()));
  ws.addEventListener('message', ev => { const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    if (m.method === 'Runtime.exceptionThrown') { const x = m.params.exceptionDetails; errors.push((x.exception && x.exception.description) || x.text); } });
  const cmd = (method, params) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expr) => { const r = await cmd('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result && r.result.exceptionDetails) throw new Error('page exception: ' + JSON.stringify(r.result.exceptionDetails)); return r.result.result.value; };
  return { cmd, ev, ready, errors, close: () => ws.close() };
}

let passed = 0, failed = 0; const fails = [];
function check(name, cond, detail) { if (cond) passed++; else { failed++; fails.push(name + (detail ? ' — ' + detail : '')); } }

const SETTLE = `(async () => { for (let i = 0; i < 300; i++) { if (!candyAnimating) return; await new Promise(r => setTimeout(r, 10)); } })()`;

async function run() {
  await ensureServer();
  const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    `--remote-debugging-port=${DBG_PORT}`, `--user-data-dir=${PROFILE}`, `${baseUrl}/shift-puzzle/`], { stdio: 'ignore' });
  let cl;
  try {
    cl = makeClient(await devtoolsWs());
    await cl.ready; await cl.cmd('Runtime.enable'); await cl.ev('1+1'); await delay(600);

    // dropdown is exactly the 5 shape modes
    const opts = await cl.ev(`[...document.getElementById('difficulty').options].map(o => o.value)`);
    check('dropdown = S1..S5', JSON.stringify(opts) === JSON.stringify(['S1', 'S2', 'S3', 'S4', 'S5']), JSON.stringify(opts));

    // A. each mode loads, plays 10 moves, stays full + feasible, no exception
    for (const S of ['S1', 'S2', 'S3', 'S4', 'S5']) {
      const r = await cl.ev(`(async () => {
        els.difficulty.value = '${S}'; applyDifficulty('${S}'); await ${SETTLE};
        if (!candy) return { ok:false, why:'not candy' };
        for (let i = 0; i < 10; i++) { doMove(['U','D','L','R','CW','CCW'][(Math.random()*6)|0]); await ${SETTLE}; }
        const cnt = {}; for (const v of state) if (v) { const c = decC(v); cnt[c] = (cnt[c]||0)+1; }
        const feasT = (cnt[candyTarget.C]||0) >= candyTarget.shape.length;
        const feasN = (cnt[candyNextTarget.C]||0) >= candyNextTarget.shape.length;
        return { ok: state.every(v => v !== 0) && feasT && feasN, match: candyCfg.match };
      })()`);
      check(`${S} loads, plays, feasible`, r && r.ok, r && r.why);
    }

    // B. repeatable undo stack: 3 non-clearing moves can each be undone in turn,
    //    each refunding a move and re-lighting the undo button.
    {
      const r = await cl.ev(`(async () => {
        els.difficulty.value = 'S4'; applyDifficulty('S4'); await ${SETTLE};
        const log = []; let guard = 0;
        while (log.length < 3 && guard++ < 40) {
          const before = { board: Array.from(state), moves: candyMoves };
          const sc = score; doMove('CW'); await ${SETTLE};
          if (score === sc && !candyLost) log.push(before); else log.length = 0;
        }
        if (log.length < 3) return { ok:false, why:'no 3 non-clearing moves' };
        let okc = 0;
        for (let k = log.length - 1; k >= 0; k--) {
          const undo = candyUndoMoveName();
          if (!undo) break;
          doMove(undo); await ${SETTLE};
          if (Array.from(state).join() === log[k].board.join() && candyMoves === log[k].moves) okc++;
        }
        return { ok: okc === 3, okc };
      })()`);
      check('repeatable undo stack', r && r.ok, r && `restored ${r.okc}/3 ${r.why || ''}`);
    }

    // C. out of moves: undo button stays clickable and unwinds the loss
    {
      const r = await cl.ev(`(async () => {
        els.difficulty.value = 'S4'; applyDifficulty('S4'); await ${SETTLE};
        let guard = 0;
        while (!candyLost && guard++ < 250) { doMove('CW'); await ${SETTLE}; }
        if (!candyLost) return { ok:false, why:'never ran out' };
        const undo = candyUndoMoveName();
        if (!undo) return { ok:false, why:'no undo when lost' };
        const btn = [...document.querySelectorAll('.frame button[data-move]')].find(b => b.dataset.move === undo);
        const inert = btn.classList.contains('spent');
        const before = candyMoves;
        doMove(undo); await ${SETTLE};
        return { ok: !inert && !candyLost && candyMoves > before, inert };
      })()`);
      check('out-of-moves undo recovers', r && r.ok, r && `inert=${r.inert} ${r.why || ''}`);
    }

    // D. dual (S5): forming BOTH shapes clears them together
    {
      const r = await cl.ev(`(async () => {
        const NAMES = ['U','D','L','R','CW','CCW'];
        els.difficulty.value = 'S5'; applyDifficulty('S5'); await ${SETTLE};
        const ap = (s,m) => applyMove(s,m); const key = s => Array.from(s).join();
        function pathBoth(){ if (bothPresent(state, candyTarget, candyNextTarget, 3)) return [];
          let f=[{s:state.slice(),p:[]}]; const seen=new Set([key(state)]); let d=0;
          while(f.length&&d<10){d++;const nf=[];for(const nd of f)for(const m of NAMES){const ns=ap(nd.s,m);const k=key(ns);const np=nd.p.concat(m);if(bothPresent(ns,candyTarget,candyNextTarget,3))return np;if(!seen.has(k)){seen.add(k);nf.push({s:ns,p:np});}}f=nf;}
          return null; }
        let cleared = 0;
        for (let attempt = 0; attempt < 12 && cleared < 1; attempt++) {
          const path = pathBoth();
          if (!path) { document.getElementById('resetBtn').click(); await ${SETTLE}; continue; }
          const sb = score;
          for (const m of path) { doMove(m); await ${SETTLE}; }
          if (path.length === 0) { doMove('CW'); await ${SETTLE}; }
          if (score > sb) cleared++;
          document.getElementById('resetBtn').click(); await ${SETTLE};
        }
        return { ok: cleared >= 1, cleared };
      })()`);
      check('dual clears both shapes', r && r.ok, r && `cleared ${r.cleared}`);
    }

    // E. partial axis (S3): fewer bars than cells (some wildcards); full (S4): all bars
    {
      const r = await cl.ev(`(async () => {
        els.difficulty.value = 'S3'; applyDifficulty('S3'); await ${SETTLE};
        let partialSeen = false;
        for (let i = 0; i < 20; i++) { document.getElementById('resetBtn').click();
          const cells = document.querySelectorAll('#shapeCur .scell.on').length;
          const bars = document.querySelectorAll('#shapeCur .scell.on .arrow.bar').length;
          if (bars > 0 && bars < cells) partialSeen = true; }
        const s3HasAxes = !!candyTarget.axes;
        els.difficulty.value = 'S4'; applyDifficulty('S4'); await ${SETTLE};
        const s4FullBars = (() => { const cells = document.querySelectorAll('#shapeCur .scell.on').length; const bars = document.querySelectorAll('#shapeCur .scell.on .arrow.bar').length; return cells > 0 && bars === cells; })();
        return { ok: partialSeen && s3HasAxes && s4FullBars, partialSeen, s3HasAxes, s4FullBars };
      })()`);
      check('partial vs full axis rendering', r && r.ok, r && JSON.stringify(r));
    }

    check('no uncaught page exceptions', cl.errors.length === 0, cl.errors.join(' | '));

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
