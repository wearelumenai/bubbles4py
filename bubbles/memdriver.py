import string
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
            self.results[result_id] = result
        return result_id

    def get_result(self, result_id):
        """
        Get a result in memory from its unique identifier
        :param result_id: the unique identifier
        :return: the result
        """
        with self._mu:
            return self.results[result_id]
