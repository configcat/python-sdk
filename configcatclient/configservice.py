import concurrent
import hashlib
import time
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Event, Lock

from configcatclient import utils
from configcatclient.configentry import ConfigEntry
from configcatclient.configfetcher import ConfigFetcher
from configcatclient.constants import CONFIG_FILE_NAME, FEATURE_FLAGS
from configcatclient.pollingmode import AutoPollingMode, LazyLoadingMode
from configcatclient.refreshresult import RefreshResult
from configcatclient.utils import get_seconds_since_epoch
import time


class ConfigService(object):
    def __init__(self, sdk_key, polling_mode, hooks, config_fetcher, log, config_cache, is_offline):
        self._sdk_key = sdk_key
        self._cached_entry = ConfigEntry.empty
        self._cached_entry_string = ''
        self._polling_mode = polling_mode
        self.log = log
        self._config_cache = config_cache
        self._hooks = hooks
        self._cache_key = hashlib.sha1(('python_' + CONFIG_FILE_NAME + '_' + self._sdk_key).encode('utf-8')).hexdigest()
        self._config_fetcher = config_fetcher
        self._is_offline = is_offline
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._response_future = None
        self._initialized = Event()
        self._lock = Lock()
        self._start_time = utils.get_utc_now()

        if isinstance(self._polling_mode, AutoPollingMode):
            self._start_poll()
        else:
            self._set_initialized()

    def get_settings(self):
        if isinstance(self._polling_mode, LazyLoadingMode):
            entry, _ = self._fetch_if_older(
                utils.get_utc_now_seconds_since_epoch() - self._polling_mode.cache_refresh_interval_seconds)
            return entry.config.get(FEATURE_FLAGS), entry.fetch_time
        elif isinstance(self._polling_mode, AutoPollingMode) and not self._initialized.is_set():
            elapsed_time = (utils.get_utc_now() - self._start_time).total_seconds()
            if elapsed_time < self._polling_mode.max_init_wait_time_seconds:
                self._initialized.wait(self._polling_mode.max_init_wait_time_seconds - elapsed_time)

                # Max wait time expired without result, notify subscribers with the cached config.
                if not self._initialized.is_set():
                    self._set_initialized()
                    return self._cached_entry.config.get(FEATURE_FLAGS), self._cached_entry.fetch_time

        entry, _ = self._fetch_if_older(utils.distant_past, prefer_cache=True)
        return entry.config.get(FEATURE_FLAGS), entry.fetch_time

    def refresh(self):
        """
        :return: Returns the RefreshResult object
        """
        _, error = self._fetch_if_older(utils.distant_future)
        return RefreshResult(is_success=error is None, error=error)

    def set_online(self):
        self._lock.acquire()
        try:
            if not self._is_offline:
                return

            self._is_offline = False
            if isinstance(self._polling_mode, AutoPollingMode):
                self._start_poll()
            self.log.debug('Switched to ONLINE mode.')
        finally:
            self._lock.release()

    def set_offline(self):
        self._lock.acquire()
        try:
            if self._is_offline:
                return

            self._is_offline = True
            if isinstance(self._polling_mode, AutoPollingMode):
                start = time.perf_counter()
                self._stopped.set()
                self._thread.join()
                end = time.perf_counter()
                ms = (end - start)
                print(f"Elapsed {ms:.03f} secs.")
            self.log.debug('Switched to OFFLINE mode.')
        finally:
            self._lock.release()

    def is_offline(self):
        return self._is_offline  # atomic operation in python (lock is not needed)

    def close(self):
        # Without this the Python interpreter cannot stop when the user writes an infinite loop
        # Even though all threads in ThreadPoolExecutor are created as daemon threads
        # They are not stopped on Python's shutdown but Python waits for them to stop on their own
        # See https://stackoverflow.com/a/49992422/13160001
        if len(concurrent.futures.thread._threads_queues) and len(self._executor._threads):
            del concurrent.futures.thread._threads_queues[list(self._executor._threads)[0]]
        self._executor.shutdown(wait=False)
        if isinstance(self._polling_mode, AutoPollingMode):
            self._stopped.set()

    def _fetch_if_older(self, time, prefer_cache=False):
        """
        :return: Returns the ConfigEntry object and error message in case of any error.
        """

        self._lock.acquire()
        try:
            # Sync up with the cache and use it when it's not expired.
            if self._cached_entry.is_empty() or self._cached_entry.fetch_time > time:
                entry = self._read_cache()
                if not entry.is_empty() and entry.etag != self._cached_entry.etag:
                    self._cached_entry = entry
                    self._hooks.invoke_on_config_changed(entry.config.get(FEATURE_FLAGS))

                # Cache isn't expired
                if self._cached_entry.fetch_time > time:
                    self._set_initialized()
                    return self._cached_entry, None

            # Use cache anyway (get calls on auto & manual poll must not initiate fetch).
            # The initialized check ensures that we subscribe for the ongoing fetch during the
            # max init wait time window in case of auto poll.
            if prefer_cache and self._initialized.is_set():
                return self._cached_entry, None

            # If we are in offline mode we are not allowed to initiate fetch.
            if self._is_offline:
                offline_warning = 'The SDK is in offline mode, it can not initiate HTTP calls.'
                self.log.warning(offline_warning)
                return self._cached_entry, offline_warning

            # No fetch is running, initiate a new one.
            # Ensure only one fetch request is running at a time.
            # If there's an ongoing fetch running, we will wait for the ongoing fetch future and use its response.
            if self._response_future is None or self._response_future.done():
                self._response_future = self._executor.submit(self._config_fetcher.get_configuration,
                                                              self._cached_entry.etag)

            response = self._response_future.result()

            if response.is_fetched():
                self._cached_entry = response.entry
                self._write_cache(response.entry)
                self._hooks.invoke_on_config_changed(response.entry.config.get(FEATURE_FLAGS))
            elif response.is_not_modified():
                self._cached_entry.fetch_time = utils.get_utc_now_seconds_since_epoch()
                self._write_cache(self._cached_entry)

            self._set_initialized()
            return self._cached_entry, None
        finally:
            self._lock.release()

    def _start_poll(self):
        self._started = Event()
        self._thread = Thread(target=self._run, args=[])
        self._thread.daemon = True  # daemon thread terminates its execution when the main thread terminates
        self._thread.start()
        self._started.wait()

    def _run(self):
        self._stopped = Event()
        self._started.set()
        while True:
            self._fetch_if_older(utils.get_utc_now_seconds_since_epoch() - self._polling_mode.auto_poll_interval_seconds)
            self._stopped.wait(timeout=self._polling_mode.auto_poll_interval_seconds)
            if self._stopped.is_set():
                break

    def _set_initialized(self):
        if not self._initialized.is_set():
            self._initialized.set()
            self._hooks.invoke_on_ready()

    def _read_cache(self):
        try:
            json_string = self._config_cache.get(self._cache_key)
            if not json_string or json_string == self._cached_entry_string:
                return ConfigEntry.empty

            self._cached_entry_string = json_string
            return ConfigEntry.create_from_json(json.loads(json_string))
        except Exception as e:
            self.log.error('An error occurred during the cache read. ' + str(e))
            return ConfigEntry.empty

    def _write_cache(self, config_entry):
        try:
            self._config_cache.set(self._cache_key, json.dumps(config_entry.to_json()))
        except Exception as e:
            self.log.error('An error occurred during the cache write. ' + str(e))
