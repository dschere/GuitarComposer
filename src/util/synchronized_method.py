import threading
from functools import wraps

def synchronized_method(func):
    """Decorator to synchronize access to an instance method using an instance lock."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Ensure the instance has a lock. Create one if it doesn't exist.
        if not hasattr(self, "_lock"):
            self._lock = threading.RLock()
        
        with self._lock:
            return func(self, *args, **kwargs)
    return wrapper