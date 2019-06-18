import unittest

from memdriver import MemDriver


class TestMemDriver(unittest.TestCase):

    def test_put_get(self):
        driver = MemDriver()
        result = {'hello': 'world'}
        id = driver.put_result(result)
        actual = driver.get_result(id)
        self.assertEqual(result, actual)
