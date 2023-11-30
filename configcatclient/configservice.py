import hashlib
from threading import Thread, Event, Lock

from . import utils
from .config import FEATURE_FLAGS, CONFIG_FILE_NAME, SERIALIZATION_FORMAT_VERSION
from .configentry import ConfigEntry
from .pollingmode import AutoPollingMode, LazyLoadingMode
from .refreshresult import RefreshResult


class ConfigService(object):
    def __init__(self, sdk_key, polling_mode, hooks, config_fetcher, log, config_cache, is_offline):
        self._cached_entry = ConfigEntry.empty
        self._cached_entry_string = ''
        self._polling_mode = polling_mode
        self.log = log
        self._config_cache = config_cache
        self._hooks = hooks
        self._cache_key = ConfigService._get_cache_key(sdk_key)
        self._config_fetcher = config_fetcher
        self._is_offline = is_offline
        self._response_future = None
        self._initialized = Event()
        self._lock = Lock()
        self._ongoing_fetch = False
        self._fetch_finished = Event()
        self._start_time = utils.get_utc_now()

        if isinstance(self._polling_mode, AutoPollingMode) and not is_offline:
            self._start_poll()
        else:
            self._set_initialized()

    def get_config(self):
        if isinstance(self._polling_mode, LazyLoadingMode):
            entry, _ = self._fetch_if_older(
                utils.get_utc_now_seconds_since_epoch() - self._polling_mode.cache_refresh_interval_seconds)
            return (entry.config, entry.fetch_time) \
                if not entry.is_empty() \
                else (None, utils.distant_past)
        elif isinstance(self._polling_mode, AutoPollingMode) and not self._initialized.is_set():
            elapsed_time = (utils.get_utc_now() - self._start_time).total_seconds()
            if elapsed_time < self._polling_mode.max_init_wait_time_seconds:
                self._initialized.wait(self._polling_mode.max_init_wait_time_seconds - elapsed_time)

                # Max wait time expired without result, notify subscribers with the cached config.
                if not self._initialized.is_set():
                    self._set_initialized()
                    return (self._cached_entry.config, self._cached_entry.fetch_time) \
                        if not self._cached_entry.is_empty() \
                        else (None, utils.distant_past)

        # If we are initialized, we prefer the cached results
        entry, _ = self._fetch_if_older(utils.distant_past, prefer_cache=self._initialized.is_set())
        return (entry.config, entry.fetch_time) \
            if not entry.is_empty() \
            else (None, utils.distant_past)

    def refresh(self):
        """
        :return: RefreshResult object
        """
        if self.is_offline():
            offline_warning = 'Client is in offline mode, it cannot initiate HTTP calls.'
            self.log.warning(offline_warning, event_id=3200)
            return RefreshResult(is_success=False, error=offline_warning)

        _, error = self._fetch_if_older(utils.distant_future)
        return RefreshResult(is_success=error is None, error=error)

    def set_online(self):
        with self._lock:
            if not self._is_offline:
                return

            self._is_offline = False
            if isinstance(self._polling_mode, AutoPollingMode):
                self._start_poll()

            self.log.info('Switched to %s mode.', 'ONLINE', event_id=5200)

    def set_offline(self):
        with self._lock:
            if self._is_offline:
                return

            self._is_offline = True
            if isinstance(self._polling_mode, AutoPollingMode):
                self._stopped.set()
                self._thread.join()

            self.log.info('Switched to %s mode.', 'OFFLINE', event_id=5200)

    def is_offline(self):
        return self._is_offline  # atomic operation in python (lock is not needed)

    def close(self):
        if isinstance(self._polling_mode, AutoPollingMode):
            self._stopped.set()

    def _fetch_if_older(self, threshold, prefer_cache=False):
        """
        :return: Returns the ConfigEntry object and error message in case of any error.
        """

        with self._lock:
            # Sync up with the cache and use it when it's not expired.
            from_cache = self._read_cache()
            if not from_cache.is_empty() and from_cache.etag != self._cached_entry.etag:
                self._cached_entry = from_cache
                self._hooks.invoke_on_config_changed(from_cache.config.get(FEATURE_FLAGS))

            # Cache isn't expired
            if self._cached_entry.fetch_time > threshold:
                self._set_initialized()
                return self._cached_entry, None

            # If we are in offline mode or the caller prefers cached values, do not initiate fetch.
            if self._is_offline or prefer_cache:
                return self._cached_entry, None

        # No fetch is running, initiate a new one.
        # Ensure only one fetch request is running at a time.
        # If there's an ongoing fetch running, we will wait for the ongoing fetch.
        if self._ongoing_fetch:
            self._fetch_finished.wait()
        else:
            self._ongoing_fetch = True
            self._fetch_finished.clear()
            response = self._config_fetcher.get_configuration(self._cached_entry.etag)

            with self._lock:
                if response.is_fetched():
                    self._cached_entry = response.entry
                    self._write_cache(response.entry)
                    self._hooks.invoke_on_config_changed(response.entry.config.get(FEATURE_FLAGS))
                elif (response.is_not_modified() or not response.is_transient_error) and \
                        not self._cached_entry.is_empty():
                    self._cached_entry.fetch_time = utils.get_utc_now_seconds_since_epoch()
                    self._write_cache(self._cached_entry)

                self._set_initialized()

            self._ongoing_fetch = False
            self._fetch_finished.set()

        return self._cached_entry, None

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
            self._fetch_if_older(utils.get_utc_now_seconds_since_epoch() - self._polling_mode.poll_interval_seconds)
            self._stopped.wait(timeout=self._polling_mode.poll_interval_seconds)
            if self._stopped.is_set():
                break

    def _set_initialized(self):
        if not self._initialized.is_set():
            self._initialized.set()
            self._hooks.invoke_on_client_ready()

    @staticmethod
    def _get_cache_key(sdk_key):
        return hashlib.sha1(
            (sdk_key + '_' + CONFIG_FILE_NAME + '.json' + '_' + SERIALIZATION_FORMAT_VERSION).encode('utf-8')).hexdigest()

    def _read_cache(self):
        try:
            json_string = self._config_cache.get(self._cache_key)
            if not json_string or json_string == self._cached_entry_string:
                return ConfigEntry.empty

            self._cached_entry_string = json_string
            return ConfigEntry.create_from_string(json_string)
        except Exception:
            self.log.exception('Error occurred while reading the cache.', event_id=2200)
            return ConfigEntry.empty

    def _write_cache(self, config_entry):
        try:
            self._config_cache.set(self._cache_key, config_entry.serialize())
        except Exception:
            self.log.exception('Error occurred while writing the cache.', event_id=2201)
