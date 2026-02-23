# queue/__init__.py
# This package intentionally re-exports from stdlib queue to avoid masking it.
# The project uses 'queue/' as a directory name, which conflicts with stdlib queue.
# Importing via importlib with explicit path to stdlib avoids circular import.
import sys
import os
import importlib.util

# Find the stdlib queue.py (it lives in the Python lib directory, not a package)
_stdlib_queue_path = None
for _p in sys.path:
    if _p and os.path.isfile(os.path.join(_p, "queue.py")):
        _candidate = os.path.join(_p, "queue.py")
        # Make sure this is not ourselves
        _our_dir = os.path.dirname(os.path.abspath(__file__))
        if not _candidate.startswith(_our_dir):
            _stdlib_queue_path = _candidate
            break

if _stdlib_queue_path:
    _spec = importlib.util.spec_from_file_location("_stdlib_queue_internal", _stdlib_queue_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    Empty = _mod.Empty
    Full = _mod.Full
    Queue = _mod.Queue
    LifoQueue = _mod.LifoQueue
    PriorityQueue = _mod.PriorityQueue
    SimpleQueue = _mod.SimpleQueue
    __all__ = ["Empty", "Full", "Queue", "LifoQueue", "PriorityQueue", "SimpleQueue"]
else:
    raise ImportError(
        "Could not find stdlib 'queue' module. "
        "The project's queue/ directory shadows it. "
        "Check your Python environment's sys.path."
    )
