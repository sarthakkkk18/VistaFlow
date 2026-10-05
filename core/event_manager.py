"""Synchronous bus; callers marshal GUI work onto its owning thread."""

import logging
from collections import defaultdict


class EventManager:
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, topic, handler):
        self._subscribers[topic].append(handler)
        return lambda: self._subscribers[topic].remove(handler)

    def publish(self, event):
        failures = []
        for handler in tuple(self._subscribers[event.type]):
            try:
                handler(event)
            except Exception as error:
                failures.append(type(error).__name__)
                logging.getLogger(__name__).warning(
                    "Event subscriber failed: %s", type(error).__name__
                )
        return failures
