import time
import threading
from typing import Callable, Optional


class MultiEventDetector:
    def __init__(
        self,
        multi_event_callback: Callable[..., None],
        debounce_delay: float = 0.3,
    ) -> None:
        self.multi_event_callback = multi_event_callback
        self.debounce_delay = debounce_delay
        self._lock = threading.Lock()
        self._last_event_time = None
        self._count = 0
        self._timer = None

    def handle_event(self, timestamp: Optional[float] = None, *args, **kwargs) -> None:
        if timestamp is None:
            timestamp = time.time()

        with self._lock:
            if (
                self._last_event_time is not None
                and (timestamp - self._last_event_time) <= self.debounce_delay
            ):
                # Cancel the active time
                if self._timer:
                    self._timer.cancel()
                    self._timer = None

            self._count += 1
            self._last_event_time = timestamp

            # Start a new timer
            self._timer = threading.Timer(
                self.debounce_delay, self._handle_multi_event, args, kwargs
            )
            self._timer.start()

    def _handle_multi_event(self, *args, **kwargs) -> None:
        with self._lock:
            self.multi_event_callback(self._count, *args, **kwargs)
            self._count = 0
            self._last_event_time = 0
            self._timer = None
