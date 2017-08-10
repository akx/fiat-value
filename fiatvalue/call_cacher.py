import shelve
import json
import time
import hashlib
from functools import wraps


class Expired(Exception):
    pass


class Cache:
    def __init__(self, name, ttl=60):
        self.shelf = shelve.open('%s.cache.shelf' % name)
        self.ttl = ttl

    def hash(self, value):
        return hashlib.sha1(json.dumps(value, sort_keys=True).encode('utf-8')).hexdigest()

    def hash_args_kwargs(self, args, kwargs):
        return self.hash([args, list(sorted(kwargs.items()))])

    def get(self, key):
        itime, value = self.shelf[key]
        lifetime = time.time() - itime
        if lifetime > self.ttl:
            raise Expired(lifetime)
        return value

    def set(self, key, value):
        self.shelf[key] = (time.time(), value)

    def retrieve_or_call(self, fn, args, kwargs):
        hash = self.hash_args_kwargs(args, kwargs)
        try:
            return self.get(hash)
        except (KeyError, Expired):
            rv = fn(*args, **kwargs)
            self.set(hash, rv)
            return rv

    def wrap_function(self, fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            return self.retrieve_or_call(fn, args, kwargs)

        return wrapped


class CallCacher:
    def __init__(self, name, target, ttl=60):
        self.__cache = Cache(name, ttl)
        self.__target = target

    def __getattr__(self, name):
        obj = getattr(self.__target, name)
        if not callable(obj):
            return obj
        return self.__cache.wrap_function(obj)
