# Shift Puzzle tests

The game (`public/shift-puzzle/index.html`) is candy SHAPE modes only (S1–S5):
Shapes (easy), Shapes, Shapes + axis (partial), Shapes + axis, Two shapes.

- **`engine.test.mjs`** — fast, no browser. Extracts the page's pure functions
  (geometry, move algebra, shape generation) and checks the invariants:
  move inverses, the turn-on-exit rotation rule + centre spin, shape feasibility
  (colour-count sufficiency, no edge-wrap), per-mode target feasibility, the
  partial-axis target structure, and dual distinct-colour generation.
  Run: `npm run test:engine`.

- **`functional.test.mjs`** — drives the *built* page in headless Chrome (CDP):
  the dropdown is exactly S1–S5, each mode loads/plays/stays feasible, the
  repeatable candy undo stack, out-of-moves undo recovery, dual clears both
  shapes, and partial-vs-full axis rendering. Requires Google Chrome at the
  macOS default path. Run: `npm run test:functional` (builds + previews itself),
  or pass a running server: `node test/functional.test.mjs http://localhost:4321`.

Run both with `npm test`.
