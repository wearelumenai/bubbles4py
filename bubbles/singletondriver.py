class SingletonDriver:
    def __init__(self, name):
        self.result = None
        self.result_id = name

    def put_result(self, result):
        self.result = result
        return self.result_id

    def get_result(self, result_id):
        if result_id == self.result_id:
            return self.result
