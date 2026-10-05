"""Normalized gesture/keyboard/UI commands operate pure filter state."""

from dataclasses import replace

from core.models import Command
from vision.live_filters import FILTERS, FilterSettings

POSE_FILTERS = {
    "OPEN_PALM": "original",
    "INDEX_POINTER": "gaussian",
    "V_SIGN": "canny",
    "THREE_FINGERS": "grayscale",
    "ROCK_SIGN": "sharpen",
    "PINKY_POINTER": "colour map",
}
GESTURE_HELP = {
    **{k: "Select " + v for k, v in POSE_FILTERS.items()},
    "FIST": "Freeze / resume preview",
    "PINCH": "Toggle before / after",
    "SWIPE_LEFT": "Previous filter",
    "SWIPE_RIGHT": "Next filter",
    "SWIPE_UP": "Brightness +10",
    "SWIPE_DOWN": "Brightness -10",
}


def gesture_command(event):
    name = event.name.upper()
    if name in POSE_FILTERS:
        return Command("SET_FILTER", "gesture", {"operation": POSE_FILTERS[name]}, event.timestamp)
    mapping = {
        "FIST": ("FREEZE", {}),
        "PINCH": ("COMPARE", {}),
        "SWIPE_LEFT": ("STEP", {"step": -1}),
        "SWIPE_RIGHT": ("STEP", {"step": 1}),
        "SWIPE_UP": ("BRIGHTNESS", {"step": 10}),
        "SWIPE_DOWN": ("BRIGHTNESS", {"step": -10}),
    }
    if name in mapping:
        intent, params = mapping[name]
        return Command(intent, "gesture", params, event.timestamp)
    return None


class FilterController:
    def __init__(self):
        self.settings = FilterSettings()
        self.compare = True
        self.frozen = False

    def dispatch(self, command):
        p = command.parameters
        if command.intent == "SET_FILTER":
            self.settings = replace(self.settings, operation=p["operation"])
        elif command.intent == "PARAMETERS":
            self.settings = replace(self.settings, **p)
        elif command.intent == "STEP":
            index = (FILTERS.index(self.settings.operation) + p["step"]) % len(FILTERS)
            self.settings = replace(self.settings, operation=FILTERS[index])
        elif command.intent == "BRIGHTNESS":
            self.settings = replace(
                self.settings, brightness=max(-100, min(100, self.settings.brightness + p["step"]))
            )
        elif command.intent == "RESET":
            self.settings = FilterSettings()
            self.frozen = False
        elif command.intent == "FREEZE":
            self.frozen = not self.frozen
        elif command.intent == "COMPARE":
            self.compare = not self.compare
        else:
            raise ValueError("Unsupported command")
        return self.settings
