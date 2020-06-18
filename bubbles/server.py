import json
import logging
import os
import signal
import time
from datetime import datetime
from threading import Thread

from bottle import Bottle, request, response, static_file

_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'root')


class Server:
    """Dataviz server"""

    def __init__(self, driver):
        """
        Create a new Server instance
        :param driver: the backend that will store the results
        """
        self.driver = driver
        self.app = Bottle()
        self.app.route('/result', method='POST', callback=self.post_result)
        self.app.route('/result/<result_id>', method='GET', callback=self.get_result)
        self.app.route('/results', method='GET', callback=self.get_results)
        self.app.route('/numlevels', method='GET', callback=self.numlevels)
        self.app.route('/detail_community/<com_id>', method='GET', callback=self.detail_community)
        self.app.route('/last_date', method='GET', callback=self.last_date)
        self.app.route('/set_level/<level>', method='GET', callback=self.set_level)
        self.app.route('/set_date/<date>', method='GET', callback=self.set_date)
        self.app.route('/bubbles', method='GET', callback=Server.get_bubbles)
        self.app.route('/graph', method='GET', callback=Server.get_graph)
        self.app.route('/sub_graph<com_id>', method='GET', callback=Server.sub_graph)
        self.app.route('/tools/<filename>', method='GET', callback=Server.get_js)
        self.app.route('/switch_com_nodeid', method='GET', callback=self.switch_com_nodeid)
        self.app.route('/stop_time', method='GET', callback=self.switch_stop_time)
        self.app.route('/get_curve', method='GET', callback=self.get_curve)
        self.process = None

    def get_curve(self):
        return self.driver.get_curve()

    def switch_stop_time(self):
        return self.driver.switch_stop_time()

    def switch_com_nodeid(self):
        return self.driver.switch_com_nodeid_func()

    def sub_graph(self, com_id):
        pass

    def last_date(self):
        return {'last_date': self.driver.get_last_date()}

    def detail_community(self, com_id):
        if getattr(self.driver, "detail_community", None):
            return self.driver.detail_community(com_id)

    def numlevels(self):
        if getattr(self.driver, "get_num_levels", None):
            num_of_levels, cur_level, num_of_com, com_id = self.driver.get_num_levels()
            result = {"num_of_levels": num_of_levels, "cur_level": cur_level, "num_of_com": num_of_com, "com_id": com_id}
        else:
            num_of_levels = 0
            result = {"num_of_levels": num_of_levels}
        return result

    def set_level(self, level):
        if getattr(self.driver, "set_level", None):
            num_of_levels, cur_level, num_of_com, com_id = self.driver.set_level(level)
            result = {"num_of_levels": num_of_levels, "cur_level": cur_level, "num_of_com": num_of_com, "com_id": com_id}
        else:
            num_of_levels = 0
            result = {"num_of_levels": num_of_levels}
        return result

    def set_date(self, date):
        if getattr(self.driver, "set_date", None):
            return self.driver.set_date(date)
        else:
            return False

 
    def post_result(self):
        """
        Callback used to store a result on a POST request
        :return: a dict containing the result id {'result_id': 'xxxx'}
        """
        result = json.load(request.body)
        result_id = self.driver.put_result(result)
        response.status = 201
        response.add_header('Location', '/result/{}'.format(result_id))
        response.content_type = 'application/json'
        return {'result_id': result_id}

    def get_result(self, result_id):
        """
        Callback used to return a result on a GET request
        :param result_id:  the unique identifier of the result
        :return: the result as a dict
        """
        return self.driver.get_result(result_id)

    def get_results(self):
        start = request.query.get('start')
        if start is not None:
            start = datetime.fromisoformat(start)
        results = self.driver.get_results(start)
        return {k: _make_response(v)
                for k, v in results.items()
                }

    @staticmethod
    def get_bubbles():
        """
        Serve the dataviz page
        :return: the html/javascript code of root/bubbles.html
        """
        return static_file('bubbles.html', root=_root)

    @staticmethod
    def get_graph():
        """
        Serve the dataviz page
        :return: the html/javascript code of root/graph.html
        """
        return static_file('graph.html', root=_root)

    @staticmethod
    def get_js(filename):
        """
        Get the javascript libraries
        :param filename: the javascript file name
        :return: the javascript library
        """
        return static_file(filename, root=_root + '/js')

    def start(self, timeout=None, **kwargs):
        """
        Start the dataviz server
        :param timeout: stop the server after the given amount of seconds,
        run forever if None (default)
        :param kwargs: parameters for the backen WSGI server
        """
        self.process = Thread(target=self.app.run, kwargs=kwargs)
        self.process.daemon = True
        self.process.start()
        time.sleep(.1)
        if timeout is not None:
            self._timeout_terminate(timeout)

    def join(self):
        """
        Wait for the server to stop
        """
        self.process.join()

    def route(self, path=None, method='GET', callback=None, name=None,
              apply=None, skip=None, **config):
        """ From Bottle documentation :

            A decorator to bind a function to a request URL. Example::

                @app.route('/hello/:name')
                def hello(name):
                    return 'Hello %s' % name

            The ``:name`` part is a wildcard. See :class:`Router` for syntax
            details.

            :param path: Request path or a list of paths to listen to. If no
              path is specified, it is automatically generated from the
              signature of the function.
            :param method: HTTP method (`GET`, `POST`, `PUT`, ...) or a list of
              methods to listen to. (default: `GET`)
            :param callback: An optional shortcut to avoid the decorator
              syntax. ``route(..., callback=func)`` equals ``route(...)(func)``
            :param name: The name for this route. (default: None)
            :param apply: A decorator or plugin or a list of plugins. These are
              applied to the route callback in addition to installed plugins.
            :param skip: A list of plugins, plugin classes or names. Matching
              plugins are not installed to this route. ``True`` skips all.

            Any additional keyword arguments are stored as route-specific
            configuration and passed to plugins (see :meth:`Plugin.apply`).
        """
        return self.app.route(path, method, callback, name,
                              apply, skip, **config)

    def _timeout_terminate(self, timeout):
        def _term(timeout):
            time.sleep(timeout)
            os.kill(os.getpid(), signal.SIGINT)
            logging.warning('timeout reached, server was terminated')

        killer = Thread(target=_term, args=(timeout,))
        killer.daemon = True
        killer.start()

def _make_response(v):
    r = v.copy()
    r['created'] = v['created'].isoformat()
    return r
