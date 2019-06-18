import json
import sqlite3
import string
from secrets import choice

sql_init = 'CREATE TABLE IF NOT EXISTS results (id PRIMARY KEY, result)'
sql_put = 'INSERT INTO results VALUES (?, ?)'
sql_get = 'SELECT result FROM results WHERE id = ?'


class SqliteDriver(object):

    def __init__(self, db=':memory:'):
        self._conn = sqlite3.connect(db)
        c = self._conn.cursor()
        c.execute(sql_init)
        c.close()

    def put_result(self, result):
        result_id = ''.join(choice(string.ascii_lowercase) for i in range(32))
        c = self._conn.cursor()
        c.execute(sql_put, (result_id, json.dumps(result)))
        return result_id

    def get_result(self, result_id):
        c = self._conn.cursor()
        c.execute(sql_get, (result_id,))
        result = c.fetchone()[0]
        return json.loads(result)