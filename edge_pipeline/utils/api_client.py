from __future__ import annotations
from typing import List, Optional
import os
import json
import time
import threading
import logging
from collections import deque

try:
    import httpx
except ImportError:
    httpx = None

from edge_pipeline.utils.types import SecurityEvent


class BufferedAPIClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout_sec: float = 3.0,
        retry_attempts: int = 3,
        buffer_path: str = "logs/local_event_buffer.jsonl",
        buffer_max: int = 5000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_sec
        self.retry_attempts = max(1, retry_attempts)
        self.buffer_path = buffer_path
        self.buffer_max = buffer_max
        self._lock = threading.Lock()
        self._buffer: deque = deque(maxlen=buffer_max)
        self._flush_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.logger = logging.getLogger("BufferedAPIClient")
        self._load_buffer_from_disk()

    def _load_buffer_from_disk(self) -> None:
        if not os.path.exists(self.buffer_path):
            return
        try:
            os.makedirs(os.path.dirname(self.buffer_path) or ".", exist_ok=True)
            with open(self.buffer_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._buffer.append(line)
        except Exception as e:
            self.logger.warning(f"Failed to load buffer: {e}")

    def _persist_buffer(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.buffer_path) or ".", exist_ok=True)
            with open(self.buffer_path, "w") as f:
                for item in list(self._buffer)[-self.buffer_max:]:
                    f.write(item + "\n")
        except Exception as e:
            self.logger.warning(f"Failed to persist buffer: {e}")

    def _post_event(self, event_dict: dict) -> bool:
        if httpx is None:
            return False
        url = f"{self.base_url}/api/v1/events"
        for attempt in range(1, self.retry_attempts + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=event_dict)
                    if 200 <= resp.status_code < 300:
                        return True
                    self.logger.warning(f"Attempt {attempt}: HTTP {resp.status_code}")
            except Exception as e:
                self.logger.warning(f"Attempt {attempt}: connection error: {e}")
            if attempt < self.retry_attempts:
                time.sleep(0.5 * attempt)
        return False

    def send_event(self, event: SecurityEvent) -> bool:
        payload = event.to_dict()
        success = self._post_event(payload)
        if not success:
            with self._lock:
                self._buffer.append(json.dumps(payload))
                self._persist_buffer()
            self.logger.info(f"Event {event.event_id} buffered (API unreachable)")
        return success

    def flush_buffer(self) -> int:
        flushed = 0
        with self._lock:
            items = list(self._buffer)
            self._buffer.clear()
        remaining: List[str] = []
        for raw in items:
            try:
                payload = json.loads(raw)
                if self._post_event(payload):
                    flushed += 1
                else:
                    remaining.append(raw)
            except Exception:
                continue
        with self._lock:
            for r in remaining:
                self._buffer.append(r)
            self._persist_buffer()
        if flushed:
            self.logger.info(f"Flushed {flushed} buffered events ({len(remaining)} still pending)")
        return flushed

    def start_background_flush(self, interval_sec: float = 10.0) -> None:
        if self._flush_thread and self._flush_thread.is_alive():
            return
        self._stop.clear()

        def _loop() -> None:
            while not self._stop.is_set():
                try:
                    self.flush_buffer()
                except Exception as e:
                    self.logger.error(f"Background flush error: {e}")
                self._stop.wait(interval_sec)

        self._flush_thread = threading.Thread(target=_loop, daemon=True)
        self._flush_thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._flush_thread:
            self._flush_thread.join(timeout=3)
        self._persist_buffer()

    def __enter__(self) -> "BufferedAPIClient":
        self.start_background_flush()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
