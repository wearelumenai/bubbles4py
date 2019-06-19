from .memdriver import MemDriver
from .sqlitedriver import SqliteDriver

# used for inferring actual driver from command line arguments
drivers = {'MemDriver': MemDriver, 'SqliteDriver': SqliteDriver}
