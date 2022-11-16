import logging
import sys
import time
from threading import Thread, Event
from requests import HTTPError
from requests import Timeout
from datetime import datetime
from datetime import timedelta

from . import utils
from .configfetcher import FetchResponse
from .readwritelock import ReadWriteLock
from .interfaces import CachePolicy

log = logging.getLogger(sys.modules[__name__].__name__)


class AutoPollingCachePolicy(CachePolicy):

    def __init__(self, config_fetcher, config_cache, cache_key,
                 poll_interval_seconds=60, max_init_wait_time_seconds=5,
                 on_configuration_changed_callback=None):
        if poll_interval_seconds < 1:
            poll_interval_seconds = 1
        if max_init_wait_time_seconds < 0:
            max_init_wait_time_seconds = 0

        self._config_fetcher = config_fetcher
        self._config_cache = config_cache
        self._cache_key = cache_key
        self._poll_interval_seconds = poll_interval_seconds
        self._max_init_wait_time_seconds = timedelta(seconds=max_init_wait_time_seconds)
        self._on_configuration_changed_callback = on_configuration_changed_callback
        self._initialized = False
        self._is_running = False
        self._start_time = utils.get_utc_now()
        self._lock = ReadWriteLock()

        self.thread = Thread(target=self._run, args=[])
        self.thread.daemon = True
        self._is_started = Event()
        self.thread.start()
        self._is_started.wait()

    def _run(self):
        self._is_running = True
        self._is_started.set()
        while True:
            self.force_refresh()
            time.sleep(self._poll_interval_seconds)
            if not self._is_running:
                break

    def get(self):
        while not self._initialized \
                and utils.get_utc_now() < self._start_time + self._max_init_wait_time_seconds:
            time.sleep(.500)

        try:
            self._lock.acquire_read()
            configuration = self._config_cache.get(self._cache_key)
            return configuration.get(FetchResponse.CONFIG) if configuration else None
        finally:
            self._lock.release_read()

    def force_refresh(self):
        try:
            old_configuration = None
            etag = ''

            try:
                self._lock.acquire_read()
                old_configuration = self._config_cache.get(self._cache_key)
                if bool(old_configuration):
                    etag = old_configuration.get(FetchResponse.ETAG, '')
                    # Cache isn't expired
                    utc_now = utils.get_utc_now()
                    if datetime.utcfromtimestamp(old_configuration.get(FetchResponse.FETCH_TIME, 0) + self._poll_interval_seconds) > utc_now:
                        self._initialized = True
                        return
            finally:
                self._lock.release_read()

            configuration_response = self._config_fetcher.get_configuration_json(etag)

            if configuration_response.is_fetched():
                configuration = configuration_response.json()
                if configuration is None or old_configuration is None or \
                        configuration.get(FetchResponse.CONFIG) != old_configuration.get(FetchResponse.CONFIG):
                    try:
                        self._lock.acquire_write()
                        self._config_cache.set(self._cache_key, configuration)
                        self._initialized = True
                    finally:
                        self._lock.release_write()

                    try:
                        if self._on_configuration_changed_callback is not None:
                            self._on_configuration_changed_callback()
                    except Exception:
                        log.exception(sys.exc_info()[0])

            if not self._initialized and old_configuration is not None:
                self._initialized = True
        except HTTPError as e:
            log.error('Double-check your SDK Key at https://app.configcat.com/sdkkey.'
                      ' Received unexpected response: %s' % str(e.response))
        except Timeout:
            log.exception('Request timed out. Timeout values: [connect: {}s, read: {}s]'.format(
                self._config_fetcher.get_connect_timeout(), self._config_fetcher.get_read_timeout()))
        except Exception:
            log.exception(sys.exc_info()[0])

    def stop(self):
        self._is_running = False
