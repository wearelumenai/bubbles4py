import unittest

import requests
from webtest import TestApp

from memdriver import MemDriver
from server import Server


class TestServer(unittest.TestCase):

    def setUp(self):
        self.result = {
            'centers': [
                [40.6, 0.5, 0.32, 2.7, 18.46, 1., 2.43, 28.47],
                [65.91, 0.54, 0.01, 2.45, 37.34, 1., 2.32, 21.68],
                [46.49, 0.59, 0.35, 2.7, 22.73, 1., 2.49, 31.62],
                [50.74, 0.27, 0.35, 2.67, 24.48, 0.99, 2.05, 28.6],
                [51.2, 0.48, 0.56, 2.82, 22.6, 0.99, 2.58, 30.63],
                [46.71, 0.45, 0.56, 2.98, 21.79, 1., 2.56, 36.21],
                [53.85, 0.54, 0.14, 1.46, 28.32, 0., 2.03, 24.19],
                [38.05, 0.47, 0.59, 2.86, 12.44, 0.98, 2.38, 32.3],
            ],
            'counts': [35513, 30320, 15310, 5792, 8119, 11805, 5739, 3708],
            'names': ['lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit']
        }
        self.driver = MemDriver()
        self.server = Server(self.driver)
        self.app = TestApp(self.server.app)

    def test_post(self):
        r = requests.post('http://localhost:8080/result', json=self.result)
        print(r.json()['result_id'])

    def test_post_result(self):
        r_post = self.app.post_json('/result', self.result)
        self.assertEqual(201, r_post.status_code)
        result_id = r_post.json['result_id']
        self.assertIsNotNone(result_id)
        self.assertEqual('/result/{}'.format(result_id),
                         r_post.headers['Location'])

    def test_get_result(self):
        result_id = self.driver.put_result(self.result)
        r_get = self.app.get('/result/{}'.format(result_id))
        self.assertEqual(200, r_get.status_code)
        self.assertEqual(self.result, r_get.json)
