# VistaFlow — Final Academic Submission

Status: **the final, approved project**, promoted on 5 October 2026 at the user's direction.

VistaFlow is now the active project directly in `E:/FRIDAY`. The folder name remains unchanged so the workspace and existing Python environment continue to work. The application is VistaFlow, not the former full F.R.I.D.A.Y. assistant.

## Run on this computer

Double-click `E:/FRIDAY/launch.cmd`, or use PowerShell:

```powershell
Set-Location 'E:/FRIDAY'
.\launch.cmd
```

Direct entry point:

```powershell
& 'E:/FRIDAY/.venv/Scripts/python.exe' 'E:/FRIDAY/main.py'
```

## What was preserved

All 58 files from the approved VistaFlow build were promoted byte-for-byte, including application code, filters, gestures, UI, model, configuration, requirements, tests and existing documentation. No feature or algorithm was changed. The code guide was retained separately and its local paths updated for this location.

Earlier mentions of “temporary”, the previous nested path, the former project's preservation, and the distribution name `vistaflow-temporary` in the original VistaFlow files describe the build's history. They do not describe its current submission status. Those files were intentionally not edited. This note is the current location/status reference.

## Submission and installation elsewhere

Use `VistaFlow_Final.zip`, not an archive of the entire workspace. It excludes the former project, migration backup, Git history, virtual environment and caches.

Extract it into a dedicated folder and create a private Python 3.12 environment there:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python main.py
```

No API keys are required. Camera activation is explicit. Voice, Air Canvas, media player and Dino are not part of the final application.

## Verification and boundaries

See `docs/FINAL_PROMOTION_REPORT.md` and `docs/final_validation/` for relocation checks and source hashes. Existing benchmark numbers remain historical measurements, not new promotion measurements. Human gesture accuracy, sustained camera operation and device-specific behavior still require the manual validation described in the supplied VistaFlow documentation.

The old project was removed from the active root layout using a reversible move. Automatic approval review blocked permanent deletion (“blocked by policy”, no further reason provided), so the old files remain only in `.friday-retired-20261005`, excluded from the submission. Git history and the existing Python environment are also retained locally.
