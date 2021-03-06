#
# * Distributed semaphore based on Memcache
#
# Lukasz Biedrycki <lukasz.biedrycki@gmail.com>
#

import logging
import memcache
import time

log = logging.getLogger(__name__)


class MemcacheSemaphore(object):

    def __init__(self, hosts, name, value=1, ttl=30, debug=False):
        if value < 0:
            raise ValueError("semaphore initial value must be >= 0")

        self.client = memcache.Client(hosts, debug=debug)
        self.name = name
        self.value = value
        self.ttl = ttl
        self.locked_bucket = None
        self.lock_time = None

    def _sem_name(self, i):
        return "%s_%s" % (self.name, i)

    def acquire(self, blocking=True):
        while True:
            for i in xrange(self.value):
                result = self.client.add(self._sem_name(i), "1", time=self.ttl)
                if result:
                    self.locked_bucket = i
                    self.lock_time = time.time()
                    return True
            if not blocking:
                break
            time.sleep(0.5)
        return False

    __enter__ = acquire

    def release(self):
        if self.lock_time + self.ttl > time.time():
            self.client.delete(
                self._sem_name(self.locked_bucket))

    def invalidate_all(self):
        for i in xrange(self.value):
            self.client.delete(self._sem_name(i))

    def __exit__(self, t, v, tb):
        self.release()
