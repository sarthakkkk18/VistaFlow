"""Optional explicit download, never invoked by startup."""

import hashlib
from pathlib import Path
from urllib.request import urlopen

URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
DIGEST = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"


def main():
    with urlopen(URL, timeout=30) as response:
        data = response.read(20_000_000)
    if hashlib.sha256(data).hexdigest() != DIGEST:
        raise ValueError("Model checksum differs. Verify official assets before updating.")
    path = Path(__file__).resolve().parents[1] / "data" / "hand_landmarker.task"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(data)
    print("Verified hand model saved:", path)


if __name__ == "__main__":
    main()
