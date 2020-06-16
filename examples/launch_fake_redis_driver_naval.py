import sys
sys.path.append('/home/paul/programmation/lumenai/bubbles4py')

from random import randint
import time

import bubbles.memdriver 
#import MemDriver
from bubbles import Server, fake_redis_driver_naval


driver = fake_redis_driver_naval.Fake_redis_driver_naval("/home/paul/programmation/lumenai/bubbles4py/naval.pck", send_edge=True)
server = Server(driver)
port = 44393 #randint(44001, 44999)
if __name__ == "__main__":
    server.start(port=port, quiet=True)
    result_id = '00000'
    print('http://localhost:{}/graph?result_id={}'.format(port, result_id))
    try:
        server.join()
    except KeyboardInterrupt:
        pass
