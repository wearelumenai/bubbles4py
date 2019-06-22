import json
import sqlite3
import string
from datetime import datetime
from secrets import choice

sql_init = 'CREATE TABLE IF NOT EXISTS results' \
           '(id PRIMARY KEY, result, meta, created)'
sql_put = 'INSERT INTO results VALUES (?, ?, ?, ?)'
sql_get_id = 'SELECT result FROM results WHERE id = ?'
sql_get_start = 'SELECT id, meta, created FROM results WHERE created > ?'


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
        binds = (
            result_id,
            json.dumps(result),
            result.get('meta'),
            datetime.now()
        )
        c.execute(sql_put, binds)
        return result_id

    def get_result(self, result_id):
        """
        Get a result in sqlite from its unique identifier
        :param result_id: the unique identifier
        :return: the result
        """
        c = self._conn.cursor()
        c.execute(sql_get_id, (result_id,))
        result = c.fetchone()[0]
        return json.loads(result)

    def get_results(self, start=None):
        if start is None:
            start = datetime.min
        c = self._conn.cursor()
        c.execute(sql_get_start, (start,))
        meta = {}
        for row in c.fetchall():
            meta[row[0]] = {
                'meta': row[1],
                'created': row[2],
            }
        return meta
