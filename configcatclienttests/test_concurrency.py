import logging
import unittest
import multiprocessing
from time import sleep

import configcatclient
from configcatclient.user import User

logging.basicConfig(level=logging.WARN)


def _manual_force_refresh(client, repeat=10, delay=0.1):
    for i in range(repeat):
        client.force_refresh()
        sleep(delay)


class ConcurrencyTests(unittest.TestCase):
    def test_concurrency_process(self):
        client = configcatclient.get('PKDVCLf-Hq-h-kCzMp-L7Q/psuH7BGHoUmdONrzzUOY7A')
        value = client.get_value('keySampleText', False, User('key'))
        print("'keySampleText' value from ConfigCat: " + str(value))

        p1 = multiprocessing.Process(target=_manual_force_refresh, args=(client,))
        p2 = multiprocessing.Process(target=_manual_force_refresh, args=(client,))
        p1.start()
        p2.start()
        p1.join()
        p2.join()

        client.close()
