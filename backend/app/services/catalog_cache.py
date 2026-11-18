"""Bounded cache for public, published subject catalogs; student state is never cached."""
import copy
import threading
import time
from functools import wraps

from sqlalchemy import event
from sqlalchemy.orm import Session

_lock = threading.RLock()
_entries = {}
_generation = 0


def invalidate_catalog(*args):
    global _generation
    with _lock:
        _generation += 1
        _entries.clear()


def track_catalog_changes(db, flush_context):
    from app.models import Grade, KnowledgePoint, KnowledgePrerequisite, Question, Subject
    if any(isinstance(item, (Grade, KnowledgePoint, KnowledgePrerequisite, Question, Subject))
           for item in list(db.new) + list(db.dirty) + list(db.deleted)):
        db.info["catalog_changed"] = True
        invalidate_catalog()


def committed_catalog(db):
    if db.info.pop("catalog_changed", False):
        invalidate_catalog()


event.listen(Session, "after_commit", committed_catalog)
event.listen(Session, "after_flush", track_catalog_changes)
event.listen(Session, "after_rollback", invalidate_catalog)


def cached_catalog(function):
    @wraps(function)
    def wrapped(db, subject_name):
        if db.info.get("catalog_changed") or db.new or db.dirty or db.deleted:
            return function(db, subject_name)
        key = (id(db.get_bind()), subject_name)
        with _lock:
            cached = _entries.get(key)
            if cached and cached[0] > time.monotonic():
                return copy.deepcopy(cached[1])
            generation = _generation
        result = function(db, subject_name)
        with _lock:
            if generation == _generation:
                if len(_entries) >= 32:
                    _entries.pop(next(iter(_entries)))
                _entries[key] = (time.monotonic() + 15, copy.deepcopy(result))
        return result
    return wrapped
