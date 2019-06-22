import time
import unittest
from datetime import datetime, timedelta

from bubbles.sqlitedriver import SqliteDriver


class TestMemDriver(unittest.TestCase):

    def setUp(self):
        self.result = {'meta': 'test'}

    def test_put_get(self):
        driver = SqliteDriver()
        result_id = driver.put_result(self.result)
        actual = driver.get_result(result_id)
        self.assertEqual(self.result, actual)

    def test_get_all(self):
        driver = SqliteDriver()
        id1 = driver.put_result(self.result)
        id2 = driver.put_result(self.result)
        results = driver.get_results()
        self.assertEqual(2, len(results))
        self.assertLess(results[id1]['created'], results[id2]['created'])

    def test_get_start(self):
        driver = SqliteDriver()
        driver.put_result(self.result)
        time.sleep(.5)
        id2 = driver.put_result(self.result)
        results = driver.get_results(datetime.now() - timedelta(seconds=.3))
        self.assertEqual(1, len(results))
        self.assertIn(id2, results)
        self.assertEqual('test', results[id2]['meta'])
