import sys
sys.path.append('/home/paul/programmation/lumenai/bubbles4py')

from random import randint
import time

import bubbles.memdriver 
#import MemDriver
from bubbles import Server, redisdriver


driver = redisdriver.GrphclusRedisDriver("elyzee_small_temp_edges.json", send_edge=True)
server = Server(driver)
port = 44394 #randint(44001, 44999)

if __name__ == "__main__":
    server.start(port=port, quiet=True)
    result_id = '00000'
    print('http://localhost:{}/bubbles?result_id={}'.format(port, result_id))
    try:
        server.join()
    except KeyboardInterrupt:
        pass
