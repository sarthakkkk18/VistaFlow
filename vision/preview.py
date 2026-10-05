"""Explicit sensor activation: python -m vision.preview. Escape exits."""

import cv2

from core.config import Config
from vision.camera import Camera


def main():
    print("CAMERA ACTIVE; frames are not saved. Escape exits.")
    try:
        with Camera(Config()) as camera:
            while True:
                frame = camera.read()
                cv2.imshow("VistaFlow CAMERA ACTIVE", frame.image)
                if cv2.waitKey(1) == 27:
                    break
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
