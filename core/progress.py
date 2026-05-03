import logging
from typing import Callable, Any, List

# Type definition for a progress callback
# e.g. callback(stage: str, level: str, message: str)
ProgressCallback = Callable[[str, str, str], Any]

class ProgressBus:
    def __init__(self):
        self._subscribers: List[ProgressCallback] = []
        self.logger = logging.getLogger("iara_progress")
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            self.logger.setLevel(logging.INFO)

    def subscribe(self, callback: ProgressCallback):
        """Add a callback to receive progress events."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: ProgressCallback):
        """Remove a callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            
    def emit(self, stage: str, level: str, message: str):
        """
        Emit a progress event to all subscribers.
        level can be 'INFO', 'WARNING', 'ERROR', etc.
        """
        # Log to standard logging first
        log_msg = f"[{stage}] {message}"
        if level.upper() == 'ERROR':
            self.logger.error(log_msg)
        elif level.upper() == 'WARNING':
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)
            
        # Notify Streamlit or other UI subscribers
        for callback in self._subscribers:
            try:
                callback(stage, level, message)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")

# Global instance for the application
_bus = ProgressBus()

def subscribe(callback: ProgressCallback):
    _bus.subscribe(callback)

def unsubscribe(callback: ProgressCallback):
    _bus.unsubscribe(callback)

def emit(stage: str, level: str, message: str):
    _bus.emit(stage, level, message)
