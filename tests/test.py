from random import randint

from bubbles.drivers import MemDriver
from bubbles import Server

result = {
    'centers': [
        [40.6, 0.5, 0.32, 2.7, 18.46, 1., 2.43, 28.47],
        [65.91, 0.54, 0.01, 2.45, 37.34, 1., 2.32, 21.68],
        [46.49, 0.59, 0.35, 2.7, 22.73, 1., 2.49, 31.62],
        [50.74, 0.27, 0.35, 2.67, 24.48, 0.99, 2.05, 28.6],
        [51.2, 0.48, 0.56, 2.82, 22.6, 0.99, 2.58, 30.63],
        [46.71, 0.45, 0.56, 2.98, 21.79, 1., 2.56, 36.21],
        [53.85, 0.54, 0.14, 1.46, 28.32, 0., 2.03, 24.19],
        [38.05, 0.47, 0.59, 2.86, 12.44, 0.98, 2.38, 32.3],
    ],
    'counts': [35513, 30320, 15310, 5792, 8119, 11805, 5739, 3708],
    'columns': ['lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit']
}

driver = MemDriver()
server = Server(driver)
port = randint(44001, 44999)

if __name__ == "__main__":
    server.start(port=port, quiet=True)

    result_id = driver.put_result(result)
    print('http://localhost:{}/bubbles?result_id={}'.format(port, result_id))
    try:
        server.join()
    except KeyboardInterrupt:
        pass
