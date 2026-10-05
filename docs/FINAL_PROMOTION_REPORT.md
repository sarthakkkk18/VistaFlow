# VistaFlow final-build promotion report

Date: 5 October 2026.

## Outcome

VistaFlow is now the active and final academic application at `E:/FRIDAY`. The approved build was relocated from `temporary/VistaFlow` to the root, without changing any of its 58 delivered files. Start it with the root `launch.cmd`. No feature, algorithm, gesture mapping, configuration default or dependency requirement was changed.

This task changes project location and submission status, not functional requirement implementation. The final project's existing requirement scope and manual-test limitations are unchanged. The former full F.R.I.D.A.Y. scope is no longer the active submission.

## Preservation

The source matched the previous VistaFlow ZIP before promotion. SHA-256 comparison verifies all 58 delivered files at the new root. The manifest is `final_validation/vistaflow_sha256.json`. Test-generated historical evidence files, if rewritten during checking, were restored to their original bytes after capturing new verification evidence separately.

The original study guide was kept as `VistaFlow_CODE_GUIDE.md` with its old absolute project paths updated. New files are `FINAL_BUILD.md`, this report, and `docs/final_validation/` with source hashes and the new test record. The distribution is `VistaFlow_Final.zip`.

Existing VistaFlow documentation/package metadata still contains historical “temporary” terminology and paths. It was deliberately left unchanged to honor the no-changes requirement. `FINAL_BUILD.md` supplies current status and setup/run instructions.

## Verification

- Isolated pytest run from the new root, with parent editable import hooks disabled: **113 passed in 10.54 seconds**. JUnit record: `final_validation/tests.xml`.
- `launch.cmd --smoke` from `E:/FRIDAY`: **exit 0**, window startup and automatic clean close succeeded.
- Ruff on `main.py core vision gesture ui experiments tests`: **one I001 import-order warning** in unchanged `tests/test_motion.py:1`; no source fix applied. Therefore a completely clean Ruff gate is not claimed.
- Exact source preservation: **58/58 files match SHA-256 baseline**.
- Final ZIP is built from an explicit source manifest plus the new final-build documents and validation evidence; it excludes the old project, virtual environment, Git data, migration backup and caches.

The smoke test did not activate physical camera capture. No new camera, gesture-accuracy or performance claim is made. Previously measured results remain in the original build evidence and have their original scope.

## Old-project removal limitation

Automatic approval review rejected recursive deletion of the old project (“blocked by policy”; no detailed reason was provided). A safer reversible replacement was completed instead: former project files were moved into `.friday-retired-20261005`, outside the active source layout and excluded from the submission ZIP and local Git discovery. Permanent deletion was **not completed**. No old voice, Canvas, media or game module remains in the active source directories.

The local `.venv` was retained so the unchanged launcher works immediately. Local `.git` history was retained; this is not included in the submission. The staging copy is retained inside the migration backup. No commit or push was performed.

## Remaining work

- Permanent removal of the excluded local backup remains unresolved because deletion was blocked.
- The single Ruff import-order warning remains intentionally unfixed under the user's no-source-changes instruction.
- Hardware/user testing remains as described by the existing VistaFlow documentation; it is unrelated to source relocation.

Promotion and byte-preservation gates passed. The requested final active build and clean submission archive are delivered; permanent old-project deletion and a clean Ruff gate are not claimed.
