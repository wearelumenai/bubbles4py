import argparse
import json
import logging
import os
import signal
import sys
import time
from multiprocessing import Process

from bottle import Bottle, request, response, static_file

from .drivers import drivers

_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'root')


class Server:

    def __init__(self, driver):
        self.driver = driver
        self.app = Bottle()
        self.app.route('/result', method='POST', callback=self.post_result)
        self.app.route('/result/<result_id>', method='GET', callback=self.get_result)
        self.app.route('/bubbles', method='GET', callback=Server.get_bubbles)
        self.app.route('/js/<filename>', method='GET', callback=Server.get_js)
        self.process = None

    def post_result(self):
        result = json.load(request.body)
        result_id = self.driver.put_result(result)
        response.status = 201
        response.add_header('Location', '/result/{}'.format(result_id))
        response.content_type = 'application/json'
        return {'result_id': result_id}

    def get_result(self, result_id):
        return self.driver.get_result(result_id)

    @staticmethod
    def get_bubbles():
        return static_file('bubbles.html', root=_root)

    @staticmethod
    def get_js(filename):
        return static_file(filename, root=_root + '/js')

    def start(self, timeout=None, **kwargs):
        self.process = Process(target=self.app.run, kwargs=kwargs)
        self.process.start()
        time.sleep(.1)
        if timeout is not None:
            self._timeout_terminate(timeout)
        else:
            self._sigint_terminate()

    def wait(self):
        self.process.join()

    def _timeout_terminate(self, timeout):
        def _term(timeout):
            time.sleep(timeout)
            self.process.terminate()
            logging.warning('timeout reached, server was terminated')

        Process(target=_term, args=(timeout,)).start()

    def _sigint_terminate(self):
        def _term(signum, frame):
            self.process.terminate()

        signal.signal(signal.SIGINT, _term)


def get_driver(driver_class, *args):
    return drivers[driver_class](*args)


def start(driver_args, server_name):
    driver = get_driver(*driver_args)
    server = Server(driver)
    server.start(server=server_name)
    server.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--driver', nargs='+', required=True)
    parser.add_argument('-s', '--server', default='gunicorn')
    args = parser.parse_args()
    sys.argv = [sys.argv[0]]

    start(args.driver, args.server)
