# Shift Puzzle tests

Two suites guard the game at `public/shift-puzzle/index.html`:

- **`engine.test.mjs`** — fast, no browser. Extracts the page's pure logic (the
  Web Worker generator + main-thread geometry) and checks the core invariants:
  move algebra, worker/main parity, exact-optimal generation, the turn-on-exit
  rotation rule, the centre spin, and shape feasibility (colour-count
  sufficiency). Run: `npm run test:engine`.

- **`functional.test.mjs`** — drives the *built* page in headless Chrome over the
  DevTools Protocol. Covers behaviour the engine tests can't: solving every level
  (L1–L15) to a win, a smoke pass over all candy modes (C1–C9), the repeatable
  candy undo stack, out-of-moves undo recovery, and shape-target feasibility.
  Requires Google Chrome at the macOS default path. Run: `npm run test:functional`
  (it builds + previews itself), or pass a running server:
  `node test/functional.test.mjs http://localhost:4321`.

Run both with `npm test`.

When you change the rotation rule, generation, or candy logic, run these — they
have already caught real regressions (and one wrong test assumption about 6×6
rings, which aren't co-periodic).
