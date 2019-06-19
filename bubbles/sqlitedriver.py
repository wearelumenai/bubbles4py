import json
import sqlite3
import string
from secrets import choice

sql_init = 'CREATE TABLE IF NOT EXISTS results (id PRIMARY KEY, result)'
sql_put = 'INSERT INTO results VALUES (?, ?)'
sql_get = 'SELECT result FROM results WHERE id = ?'


class SqliteDriver(object):
    """Sqlite backend storage for results"""

    def __init__(self, db=':memory:'):
        """
        Create a new SqliteDriver instance
        :param db:
        """
        self._conn = sqlite3.connect(db)
        c = self._conn.cursor()
        c.execute(sql_init)
        c.close()

    def put_result(self, result):
        """
        Store a result in sqlite and return a unique identifier
        :param result: the result to be stored
        :return: a unique identifier for the result
        """
        result_id = ''.join(choice(string.ascii_lowercase) for i in range(32))
        c = self._conn.cursor()
        c.execute(sql_put, (result_id, json.dumps(result)))
        return result_id

    def get_result(self, result_id):
        """
        Get a result in sqlite from its unique identifier
        :param result_id: the unique identifier
        :return: the result
        """
        c = self._conn.cursor()
        c.execute(sql_get, (result_id,))
        result = c.fetchone()[0]
        return json.loads(result)