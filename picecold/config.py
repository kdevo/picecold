import atexit
import configparser
import json
import logging
import multiprocessing
import os

import main


class Configuration:
    # The two conversion values define how the timing is stored - per default it's second/kilobyte
    TIME_CONVERT = 1  # second
    SIZE_CONVERT = 1000  # KB

    MAX_TIMINGS_PER_KEY = 5
    _TIMING_KEY_SIGN = 'sign'
    _TIMING_KEY_DESERIALIZE = 'deserialize'

    def __init__(self, cfg_dict: configparser.ConfigParser):
        # TODO: Validate settings
        self._cfg = cfg_dict
        self._load_trusted_uuids()
        self._load_timings()

    @property
    def display_type(self):
        return self._cfg['Display']['type']

    @property
    def transaction_dir(self):
        return self._cfg['Transaction']['directory']

    @property
    def unsigned_pattern(self):
        return self._cfg['Transaction']['unsigned_pattern']

    @property
    def signed_suffix(self):
        return self._cfg['Transaction']['signed_suffix']

    @property
    def electrum_path(self):
        return self._cfg['Electrum']['electrum_path']

    @property
    def wallet_password(self):
        return self._cfg['Electrum']['wallet_password']

    def _load_timings(self):
        self._timings = json.loads(self._cfg.get('Stats', 'electrum_timings', fallback="{}"))

    def _calc_timings_avg(self, key):
        """Get average result of benchmarks.

        Args:
            key: can either be _TIMING_KEY_SIGN or _TIMING_KEY_DESERIALIZE

        Returns:
             Average (s per kb size of transaction)
        """
        self._load_timings()
        timing = self._timings.get(key)
        if timing is None:
            return None
        else:
            return round(sum(timing) / len(timing), 2)

    @property
    def deserialize_time_average(self):
        """Get average deserialization timing per (s per kb)

        Returns:
            Average deserialization time (s per kb size of transaction)
        """
        avg = self._calc_timings_avg(Configuration._TIMING_KEY_DESERIALIZE)
        return avg if avg else 10 / (multiprocessing.cpu_count() / 2)  # more or less pessimistic fallback

    @property
    def sign_time_average(self):
        """Get average deserialization timing (s per kb)

        Returns:
            Average deserialization time (ms per kb size of transaction)
        """
        avg = self._calc_timings_avg(Configuration._TIMING_KEY_SIGN)
        return avg if avg else 20 / (multiprocessing.cpu_count() / 2)  # more or less pessimistic fallback

    @staticmethod
    def calc_estimated_time(timing, tx_path) -> float:
        """Utility function to get estimated time for a transaction

        Returns:
            Estimated time in seconds
        """
        return timing * (os.stat(tx_path).st_size / Configuration.SIZE_CONVERT)

    def add_sign_timing(self, measured_seconds, tx_path):
        self._add_timing(Configuration._TIMING_KEY_SIGN, measured_seconds, tx_path)

    def add_deserialize_timing(self, measured_seconds, tx_path):
        self._add_timing(Configuration._TIMING_KEY_DESERIALIZE, measured_seconds, tx_path)

    def _add_timing(self, timing_key, measured_seconds, tx_path):
        file_size = os.stat(tx_path).st_size
        # The definition of a "timing"
        timing = (measured_seconds / Configuration.TIME_CONVERT) / (file_size / Configuration.SIZE_CONVERT)
        # Save the measured value in a list which behaves like a queue with a max. amount of items MAX_TIMINGS_PER_KEY:
        if not isinstance(self._timings.get(timing_key), list):
            self._timings[timing_key] = [timing]
        elif len(self._timings[timing_key]) <= Configuration.MAX_TIMINGS_PER_KEY:
            self._timings[timing_key].insert(0, timing)
        else:
            self._timings[timing_key].insert(0, timing)
            self._timings[timing_key].pop(len(self._timings[timing_key]) - 1)
        self._cfg['Stats']['electrum_timings'] = json.dumps(self._timings)
        self._load_timings()

    def add_trusted_uuid(self, uuid):
        self._trusted_uuids.add(uuid)
        self._cfg['USB']['trusted_uuids'] = json.dumps(list(self._trusted_uuids))
        self._load_trusted_uuids()

    def _load_trusted_uuids(self):
        self._trusted_uuids = set(json.loads(self._cfg.get('USB', 'trusted_uuids', fallback="[]")))

    def is_trusted_uuid(self, uuid):
        return uuid in self._trusted_uuids


class ConfigurationManager:
    def __init__(self, file_path, save_on_exit=True):
        self._file_path = file_path
        self._save_on_exit = save_on_exit
        self._cfg_dict = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        self.load_configuration()
        self._configuration = Configuration(self._cfg_dict)

    @property
    def configuration(self) -> Configuration:
        return self._configuration

    def save_configuration(self):
        with open(self._file_path, 'w') as cfg_file:
            self._cfg_dict.write(cfg_file)

    def _save_on_exit_now(self):
        logging.info("{0} has been exited. Saving configuration to \"{1}\".", main.PLUGIN_NAME, self._file_path)
        self.save_configuration()

    def load_configuration(self):
        self._cfg_dict.read(self._file_path)

    @property
    def save_on_exit(self):
        return self._save_on_exit

    @save_on_exit.setter
    def save_on_exit(self, enable):
        if enable:
            atexit.register(self.save_configuration, True)
        else:
            atexit.unregister(self.save_configuration)
