import unittest

from bubbles.sqlitedriver import SqliteDriver


class TestMemDriver(unittest.TestCase):

    def test_put_get(self):
        driver = SqliteDriver()
        result = {'hello': 'world'}
        result_id = driver.put_result(result)
        actual = driver.get_result(result_id)
        self.assertEqual(result, actual)
