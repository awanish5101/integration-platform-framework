"""
Token Bucket rate limiter safeguarding platform endpoints against noisy-neighbor overload.
"""
import time
import threading
from typing import Dict, Tuple


class TokenBucket:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity          # Maximum burst capacity
        self.fill_rate = fill_rate        # Tokens added per second
        self.tokens = float(capacity)
        self.last_update = time.time()

    def consume(self, amount: int = 1) -> Tuple[bool, int, float]:
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Refill tokens based on time passed
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.fill_rate)

        if self.tokens >= amount:
            self.tokens -= amount
            remaining = int(self.tokens)
            return True, remaining, 0.0
        else:
            missing = amount - self.tokens
            retry_after = missing / self.fill_rate
            return False, 0, round(retry_after, 2)


class RateLimiter:
    def __init__(self, default_rpm: int = 600, burst_capacity: int = 50):
        self.default_rpm = default_rpm
        self.burst_capacity = burst_capacity
        self.fill_rate = default_rpm / 60.0
        self._lock = threading.Lock()
        self._buckets: Dict[str, TokenBucket] = {}

    def check_rate_limit(self, identifier: str, cost: int = 1) -> Tuple[bool, int, int, float]:
        """
        Returns (is_allowed, limit_rpm, remaining, retry_after_seconds)
        """
        with self._lock:
            if identifier not in self._buckets:
                self._buckets[identifier] = TokenBucket(
                    capacity=self.burst_capacity,
                    fill_rate=self.fill_rate
                )
            bucket = self._buckets[identifier]
            allowed, remaining, retry_after = bucket.consume(cost)
            return allowed, self.default_rpm, remaining, retry_after

    def reset(self):
        with self._lock:
            self._buckets.clear()


rate_limiter = RateLimiter()
