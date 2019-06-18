import string
from secrets import choice


class MemDriver:

    def __init__(self):
        self.results = {}

    def put_result(self, result):
        result_id = ''.join(choice(string.ascii_lowercase) for i in range(32))
        self.results[result_id] = result
        return result_id

    def get_result(self, id):
        return self.results[id]
