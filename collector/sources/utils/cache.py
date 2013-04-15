import os

from datetime import timedelta
from time import time, ctime

debug = 0

class RequestCache:
    cache_path = None

    def __init__ (self, cache_path):
        self.cache_path = cache_path
        if not os.path.exists (self.cache_path):
            os.makedirs (self.cache_path)

    def write (self, f, c):
        filename = "%s/%s" % (self.cache_path, f);

        fp = open (filename, "w")
        fp.write (c)

    def read (self, f):
        filename = "%s/%s" % (self.cache_path, f);

        fp = open (filename, "r")
        c = fp.read ()
        fp.close ()

        return c

    def exists (self, f):
        filename = "%s/%s" % (self.cache_path, f);
        return os.path.exists (filename)

    def expired (self, f, expiry):
        filename = "%s/%s" % (self.cache_path, f)
        curr = time ()
        cache = os.path.getmtime (filename)

        expiry = self.__cache_timedelta_to_seconds__ (expiry)

        elapsed = curr - cache

        if debug > 0: print "cache for %s downloaded %s seconds "\
                "ago and should be valid by %s seconds. %s"\
                % (f, elapsed, expiry, 'redownload' if elapsed > expiry else 'keep')

        return elapsed > expiry

    def __cache_timedelta_to_seconds__ (self, period):
        return period.days * 86400 + period.seconds
