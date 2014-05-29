"""uWSGI cache backend"""

from django.core.cache.backends.base import BaseCache, InvalidCacheBackendError
from django.conf import settings

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import uwsgi
except ImportError:
    if getattr(settings, "UWSGI_CACHE_FALLBACK", True):
        uwsgi = None
    else:
        raise InvalidCacheBackendError(
            "You're not running under uWSGI ! "
            "Set UWSGI_CACHE_FALLBACK=True in settings if you want to fallback "
            "to LocMemCache."
        )

if uwsgi:
    class UWSGICache(BaseCache):
        def __init__(self, location, params):
            BaseCache.__init__(self, params)
            self._location = location

        def has_key(self, key, version=None):
            key = self.make_key(key, version)
            return uwsgi.cache_exists(key, self._location)

        def add(self, key, value, timeout=0, version=None):
            key = self.make_key(key, version)
            if uwsgi.cache_exists(key, self._location):
                return False
            uwsgi.cache_set(key, value, timeout, self._location)

        def get(self, key, default=None, version=None):
            key = self.make_key(key, version)
            val = uwsgi.cache_get(key, self._location)
            return default if val is None else pickle.loads(val)

        def set(self, key, value, timeout=0, version=None):
            key = self.make_key(key, version)
            uwsgi.cache_update(key, pickle.dumps(value), timeout, self._location)

        def delete(self, key, version=None):
            key = self.make_key(key, version)
            uwsgi.cache_del(key, self._location)

        def clear(self):
            uwsgi.cache_clear (self._location)
else:
    from django.core.cache.backends.locmem import LocMemCache as UWSGICache
