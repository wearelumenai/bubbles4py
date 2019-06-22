import string
from datetime import datetime
from secrets import choice
from threading import Lock


class MemDriver:
    """In memory backend for result storage"""

    def __init__(self):
        """
        Create a new MemDriver instance
        """
        self.results = {}
        self._mu = Lock()

    def put_result(self, result):
        """
        Store a result in memory and return a unique identifier
        :param result: the result to be stored
        :return: a unique identifier for the result
        """
        result_id = ''.join(choice(string.ascii_lowercase) for i in range(32))
        with self._mu:
            self.results[result_id] = _make_record(result)
        return result_id

    def get_result(self, result_id):
        """
        Get a result in memory from its unique identifier
        :param result_id: the unique identifier
        :return: the result
        """
        with self._mu:
            return self.results[result_id]['result']

    def get_results(self, start=None):
        return {
            k: _make_meta(v)
            for k, v in self.results.items()
            if start is None or v['created'] > start
        }


def _make_record(result):
    return {
        'result': result,
        'created': datetime.now(),
        'meta': result.get('meta')
    }


def _make_meta(record):
    return {k: v for k, v in record.items() if k != 'result'}
