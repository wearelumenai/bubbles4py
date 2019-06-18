import string
from secrets import choice
from threading import Lock


class MemDriver:

    def __init__(self):
        self.results = {}
        self._mu = Lock()

    def put_result(self, result):
        result_id = ''.join(choice(string.ascii_lowercase) for i in range(32))
        with self._mu:
            self.results[result_id] = result
        return result_id

    def get_result(self, id):
        with self._mu:
            return self.results[id]
