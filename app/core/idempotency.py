"""
Idempotency manager ensuring safe retries for mutation endpoints in API V2.
"""
import hashlib
import json
import time
import threading
from typing import Dict, Any, Optional, Tuple


class IdempotencyRecord:
    def __init__(self, key: str, payload_hash: str, ttl: int = 86400):
        self.key = key
        self.payload_hash = payload_hash
        self.in_flight = True
        self.response_status: Optional[int] = None
        self.response_body: Optional[Dict[str, Any]] = None
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class IdempotencyManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[str, IdempotencyRecord] = {}

    def compute_hash(self, body: Any) -> str:
        if body is None:
            return ""
        if isinstance(body, bytes):
            return hashlib.sha256(body).hexdigest()
        serialized = json.dumps(body, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def acquire_lock(self, key: str, payload_hash: str, ttl: int = 86400) -> Tuple[bool, Optional[IdempotencyRecord]]:
        """
        Attempts to acquire an idempotency lock for the given key.
        Returns (is_new_request, existing_record).
        """
        with self._lock:
            # Clean expired records opportunistically
            now = time.time()
            expired_keys = [k for k, v in self._store.items() if v.is_expired()]
            for k in expired_keys:
                del self._store[k]

            existing = self._store.get(key)
            if existing:
                # If key exists and payload hash matches
                if existing.payload_hash != payload_hash:
                    # Same idempotency key used with different payload!
                    raise ValueError("Idempotency key reused with different request payload.")
                return False, existing

            # Brand new key
            record = IdempotencyRecord(key, payload_hash, ttl)
            self._store[key] = record
            return True, None

    def store_response(self, key: str, status_code: int, response_body: Dict[str, Any]):
        with self._lock:
            record = self._store.get(key)
            if record:
                record.in_flight = False
                record.response_status = status_code
                record.response_body = response_body

    def release_on_error(self, key: str):
        with self._lock:
            if key in self._store and self._store[key].in_flight:
                del self._store[key]


idempotency_manager = IdempotencyManager()
