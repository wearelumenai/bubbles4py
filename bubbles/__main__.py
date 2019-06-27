import argparse
import sys

from . import Server
from .drivers import drivers


def get_driver(driver_class, *args):
    return drivers[driver_class](*args)


def start(driver_args, server_name):
    driver = get_driver(*driver_args)
    server = Server(driver)
    server.start(server=server_name, port=49449, quiet=True)
    try:
        server.join()
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--driver', nargs='+', required=True)
    parser.add_argument('-s', '--server', nargs='+', default=['gunicorn'])
    args = parser.parse_args()
    sys.argv = [sys.argv[0], *args.server[1:]]
    start(args.driver, args.server[0])


if __name__ == "__main__":
    main()
