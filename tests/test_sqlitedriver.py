import time
import unittest
from datetime import datetime, timedelta

from bubbles.sqlitedriver import SqliteDriver


class TestMemDriver(unittest.TestCase):

    def test_put_get(self):
        driver = SqliteDriver()
        result_id = driver.put_result(self.result)
        actual = driver.get_result(result_id)
        self.assertEqual(result, actual)
