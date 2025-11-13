import logging
import sys
import unittest
import multiprocessing
from time import sleep

import pytest

import configcatclient
from configcatclient.user import User

logging.basicConfig(level=logging.WARN)


def _manual_force_refresh(sdk_key, repeat=10, delay=0.1):
    client = configcatclient.get(sdk_key)
    for _ in range(repeat):
        client.force_refresh()
        sleep(delay)


class ConcurrencyTests(unittest.TestCase):

    def test_concurrency_process(self):
        sdk_key = "PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A"
        client = configcatclient.get(sdk_key)
        value = client.get_value('keySampleText', False, User('key'))
        print("'keySampleText' value from ConfigCat: " + str(value))

        p1 = multiprocessing.Process(target=_manual_force_refresh, args=(sdk_key,))
        p2 = multiprocessing.Process(target=_manual_force_refresh, args=(sdk_key,))
        p1.start()
        p2.start()
        p1.join()
        p2.join()

        client.close()

        self.assertEqual(p1.exitcode, 0, f"Process {p1.pid} exited with code {p1.exitcode}")
        self.assertEqual(p2.exitcode, 0, f"Process {p2.pid} exited with code {p2.exitcode}")
