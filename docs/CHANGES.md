# VistaFlow — change and verification report

Date: 2026-09-29. Scope: user-requested temporary image/video processing edition.
The parent F.R.I.D.A.Y. project remains the full application. This edition is deliberately
not a replacement implementation of its complete SRS. The user-authorized scope removes
features only from this separate folder; it does not amend authoritative SRS/SDD/DFD files.

## Preservation and delivery

Created `E:/FRIDAY/temporary/VistaFlow`. Before making the copy, read AGENTS and the
engineering architecture/requirements/data flow/roadmap/standards, build state and the
three authoritative DOCX contents. Baseline original tests: 159 passed, 1 intentional
hardware skip in 21.55 s. A manifest fingerprints 173 original project source/config/docs/
evidence files. After implementation all 173 match; no missing or changed files.
See original_manifest.json and evidence/preservation.json. Caches/interpreter runtime
files are outside that source-preservation guarantee. No original source, docs or settings
were edited; no secrets copied; no repository reset or commits made.

Delivery includes a separate source ZIP, local launcher, own requirements, own config,
copied hand model, tests, screenshots and measured evidence. The original project remains
at E:/FRIDAY with voice, Canvas, media, Dino and all existing features.

## Changes and rationale

Removed from the temporary edition: voice assistant, speech recognition/synthesis,
microphone capture, assistant language layer, Air Canvas, object manipulation, media player
and shared assistant settings. Dino is also outside this focused IVP edition; the full
project retains it. No hidden UI buttons or dormant modules substitute for removal.
No direct speech-service packages are requested. MediaPipe can transitively install
sounddevice; there is no microphone/audio feature in VistaFlow.

Rebranded title, launcher and main experience as **VistaFlow — Real-Time Image & Video
Processing**. Camera/image comparison is central; side panels expose filters and gesture
help. Independent copied modules separate vision, gesture, normalized control, runtime,
UI and experiments. Eight poses and four swipes emit events, which core/control.py maps
to normalized Commands and a pure FilterController. Gesture code has no widget dependency.

Filter enhancements: 29 single-frame operations plus temporal motion; brightness/contrast
preprocessing, tunable kernels and Canny thresholds, adjustable unsharp masking, CLAHE,
bilateral smoothing, grayscale and Turbo colour map. The copied academic NumPy/OpenCV
functions remain available and tested. The live mean/sharpen path intentionally uses
parameterized OpenCV implementations; no speedup claim is inferred from that choice.
Motion reports actual frame-to-frame phase-correlation displacement. Original/processed
packets include an immutable settings snapshot so stale frames cannot appear with new
filter settings. Input images remain unchanged. Heavy processing/loading is off the Qt
thread; camera uses a bounded latest-frame queue. Freeze does not halt tracking.

Gesture changes: four new static classes (V_SIGN, THREE_FINGERS, ROCK_SIGN, PINKY_POINTER)
augment OPEN_PALM, FIST, PINCH and INDEX_POINTER. Median/EMA smoothing, palm normalization,
quality gating, hold/release FSM, pinch hysteresis, cooldown and loss recovery are retained.
The extra classes use finger-extension patterns; no neural classifier, LLM or accuracy
estimate is introduced. Removed the canvas-specific continuous/delete/two-hand channels
from the temporary recognizer. Four directional swipes remain. See README for mappings.

## Files created

All files are under the new folder; zero modified parent files.

- main.py, launch.cmd, pyproject.toml, requirements.txt, config.example.json, .gitignore.
- core/config.py, control.py, runtime.py and copied models/event_manager contracts.
- vision/: independent copies of all academic modules; new live_filters.py parameter and
  image-loading adapter; renamed standalone preview window.
- gesture/: copied hand_tracking/features/swipe modules with extended pose geometry and
  a vision-only temporal gesture_recognition.py.
- ui/: focused main_window plus shared theme/components/font helpers; no assistant panels.
- experiments/: benchmark.py, copied benchmarks.py, setup_model.py and verify.py.
- tests/: copied IVP/motion/tracking regressions plus test_vistaflow and test_desktop.
- README, docs/PLAN, docs/BUILD_STATE, this report, preservation manifest and evidence.
- data/hand_landmarker.task: a byte copy of the existing verified model, not a link to parent.

## Verification and actual results

| Check | Result |
|---|---|
| Original baseline | 159 passed, 1 hardware skip, 21.55 s |
| Final isolated VistaFlow suite | 113 passed, 5.47 s; evidence/tests.xml |
| Ruff check and format | Passed |
| Native launch.cmd --smoke | Successful startup and clean exit |
| Qt screenshot review | 1380×860 and 1080×720 reviewed; scrollable controls remain accessible |
| Installed MediaPipe model | Blank-frame inference test passed; live run also exercised inference |
| Missing model/camera | Filters continue; failure feedback and worker cleanup tested |
| Original source preservation | 173 fingerprints unchanged |
| Synthetic benchmark | All 29 single-frame choices executed; 2 warmups + 10 measured calls each |
| Live camera + MediaPipe + Canny | 60 frames; camera released; no images persisted |

The initial copied motion test accidentally resolved a benchmark helper through the
original editable-install finder. This was caught during isolation review, corrected by
copying the standalone helper, and tested with that finder removed. A module-origin test
now asserts all loaded project modules resolve inside VistaFlow. Initial compact source
formatting was normalized with Ruff. There are no known failing automated checks.

Environment: Windows 11 build 26200, Python 3.12.8. These are short measurements, not
recognition accuracy, a sustained performance guarantee, or before/after speed comparisons.

| Measured workload | Median | p95 |
|---|---:|---:|
| Camera capture cadence, 50 summaries after 10 warmups | 22.70 FPS | 24.98 FPS |
| Processed FPS, live Canny + tracking | 21.46 FPS | 21.67 FPS |
| Live processing, excluding camera read | 42.03 ms | 57.18 ms |
| Gaussian, generated 256×256 BGR | 1.313 ms | 1.362 ms |
| Canny, generated 256×256 BGR | 1.629 ms | 1.772 ms |
| CLAHE, generated 256×256 BGR | 3.058 ms | 3.249 ms |
| Bilateral, generated 256×256 BGR | 2.193 ms | 2.414 ms |
| Colour map, generated 256×256 BGR | 1.867 ms | 2.016 ms |

Raw settings, samples and machine details: evidence/filters.json and live_camera.json.
The live run requested 640×480 at 30 FPS; it did not achieve 30 processed FPS. Camera FPS
is worker acquisition cadence, not standalone device maximum. UI presentation latency,
new-pose human accuracy and false-positive rate were not measured.

## Requirements addressed and architecture

Adapted FR-01 startup, FR-03 event/action routing, FR-04 acquisition, FR-05–FR-14 academic
IVP and motion, FR-15 tracking, FR-16 expanded gestures, FR-21 visual feedback and FR-22
measured experiments. Preserved NFR modularity/privacy, configuration, testability and
optional-module isolation. Full-project FR-02/17/18/19/20 and spoken feedback are deliberately
out of scope here, retained unchanged in the original. Do not use this temporary edition
to claim complete original SRS acceptance.

Flow: camera → vision processing and hand tracking → normalized GestureEvent → Command
mapping → filter state → runtime settings snapshot → paired Qt preview. Loaded image
and synthetic sample paths share the parameter adapter; they do not require a camera.
No input module directly manipulates widgets; no camera data persistence added.

## Limitations, manual checks and exact remaining work

Implementation and feasible test/runtime gates pass. Human gesture reliability still
requires trials: each pose/swipe ten times per hand under your camera/lighting; hold each
pose five seconds to test one-shot behavior; brief occlusion and camera restart; verify
no accidental preview toggles. Tune JSON thresholds from observations. New poses have
synthetic geometry evidence only; the live inference run is not an accuracy evaluation.

Native focus, 150/200% DPI, 30-minute combined use and camera unplug/replug require manual
validation. Finger-extension heuristics remain sensitive to orientation/occlusion; the
handedness score is only a quality proxy. Swipes follow unmirrored image directions. Opening
palm resets to Original before a swipe; wait through the hold/cooldown before moving.
Haar needs even image dimensions. No local video-file playback or video export is added;
video processing here means live webcam frames. Native camera calls may delay shutdown.
Optional MediaPipe failure disables gestures but leaves filters working. No physical
interaction accuracy, guaranteed FPS, or clean-machine dependency install is claimed.

Follow README for run/setup, parameter meanings and the short demo. Do not install this
package into the same environment as the full project; the launcher may reuse its interpreter
without installing anything. A copied/extracted edition should use a private .venv.

Definition of Done: separate runnable temporary build, requested feature removals, enhanced
filters, expanded recognized poses, tests and preservation evidence complete. Human gesture
acceptance remains explicitly unverified. No changes are required to recover the original.
