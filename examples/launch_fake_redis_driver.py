import sys
sys.path.append('/home/paul/programmation/lumenai/bubbles4py')

import argparse

from random import randint
import time

import bubbles.memdriver 
#import MemDriver
from bubbles import Server, fake_redis_driver_naval

def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help='Random by default', default=randint(44001, 44999))
    parser.add_argument('pickle', help='pickle file path')
    return parser.parse_args()


def main():
    args = parseargs()

    driver = fake_redis_driver_naval.Fake_redis_driver_naval(args.pickle, send_edge=True)

    server = Server(driver)

    server.start(port=args.port, quiet=True)
    # result_id = '00000'
    #print('http://localhost:{}/graph?result_id={}'.format(port, result_id))
    print('http://localhost:{}/graph'.format(args.port))

    try:
        server.join()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
