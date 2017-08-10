import shelve
import json
import time
import hashlib
from functools import wraps

class CallCacher:
    def __init__(self, name, target, ttl=60):
        self.__shelf = shelve.open('%s.cache.shelf' % name)
        self.__target = target
        self.__ttl = ttl

    def __getattr__(self, name):
        obj = getattr(self.__target, name)
        if not callable(obj):
            return obj
        return self.__wrap_fn(obj)

    def __wrap_fn(self, fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            vals = [args, list(sorted(kwargs.items()))]
            hash = hashlib.sha1(json.dumps(vals).encode('utf-8')).hexdigest()
            rv = self.__shelf.get(hash)
            if rv:
                if time.time() - rv[0] < self.__ttl:
                    return rv[1]
            rv = fn(*args, **kwargs)
            self.__shelf[hash] = (time.time(), rv)
            return rv
        return wrapped
