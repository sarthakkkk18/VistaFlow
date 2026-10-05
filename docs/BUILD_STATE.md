# VistaFlow build state

2026-09-29 — temporary derivative, not a replacement of the full FRIDAY project.
Source audit/read-only baseline gate: 159 original tests passed, 1 skipped.
Isolation gate: dedicated copied modules/config/model and 173-file preservation manifest.
Filter/gesture gate: actual parameterized filters plus eight static poses/four swipes,
normalized Command boundary, smoothing/hold/release/cooldown retained, pure tests passed.
Qt/runtime gate: image loading/filter work off UI thread, paired comparison, freeze,
failure isolation, screenshots at 1380x860/1080x720 and native launch smoke passed.
Final automated gate: 113 tests passed in 5.47s with parent editable fallback removed;
Ruff passed. Actual 29-filter synthetic benchmark and 60-frame live Canny+tracking run
completed. Median live processed FPS 21.46. No frames saved; camera released.
Preservation gate: all 173 original file hashes match. Parent documents/source unchanged.
Final report: CHANGES.md. Human accuracy, DPI/focus and sustained live-use checks remain
manual; no gesture accuracy or performance speedup claimed. Full-project requirements
removed by this edition's authorized scope remain implemented in the unchanged parent.
