from datetime import *
import time
import unittest

from bubbles.memdriver import MemDriver


class TestMemDriver(unittest.TestCase):

    def test_put_get(self):
        driver = MemDriver()
        result_id = driver.put_result(self.result)
        actual = driver.get_result(result_id)
        self.assertEqual(result, actual)
