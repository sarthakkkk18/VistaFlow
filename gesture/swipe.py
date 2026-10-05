"""Time, distance, velocity and axis-consistency gated swipes with optional vertical directions."""

from collections import deque


class SwipeDetector:
    def __init__(self, distance=0.2, window=0.5, velocity=0.55, vertical=False):
        self.vertical = vertical
        self.distance = distance
        self.window = window
        self.velocity = velocity
        self.samples = deque()

    def update(self, x, y, timestamp):
        self.samples.append((timestamp, x, y))
        while self.samples and timestamp - self.samples[0][0] > self.window:
            self.samples.popleft()
        t, old_x, old_y = self.samples[0]
        dt = timestamp - t
        dx = x - old_x
        if (
            dt > 0
            and abs(dx) >= self.distance
            and abs(dx) / dt >= self.velocity
            and abs(y - old_y) < self.distance / 2
        ):
            self.reset()
            return "swipe_right" if dx > 0 else "swipe_left"
        dy = y - old_y
        if (
            self.vertical
            and dt > 0
            and abs(dy) >= self.distance
            and abs(dy) / dt >= self.velocity
            and abs(dx) < self.distance / 2
        ):
            self.reset()
            return "swipe_down" if dy > 0 else "swipe_up"
        return None

    def reset(self):
        self.samples.clear()
