"""Run tests without any editable-package fallback to the original project."""

import os
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    sys.path.insert(0, str(root))
    sys.meta_path[:] = [
        finder
        for finder in sys.meta_path
        if not getattr(finder, "__module__", "").startswith("__editable__")
    ]
    import pytest

    raise SystemExit(
        pytest.main(
            [str(root / "tests"), "-q", "--junitxml=" + str(root / "docs/evidence/tests.xml")]
        )
    )
