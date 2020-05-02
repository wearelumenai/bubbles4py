from datetime import *
import time, json
import unittest

from bubbles import redisdriver


class TestMemDriver(unittest.TestCase):

    def setUp(self):
        d = json.load(open('elyzee_small_temp_edges.json'))
        self.twitterActivities = d['edges'][:10]
        self.nodes = list(set([ t['source'] for t in twitterActivities ]  + [ t['target'] for t in twitterActivities ] ))
        self.communities = {1: set(nodes[:4]), 2: set(nodes[4:]) }
        self.result = {'meta': 'test'}
        self.centroids_past = [[4,5,4,5],[1,2,1,2],[6,7,6,7],[0,1,0,1]]
        self.centroids = [[1,2,1,2],[4,5,4,5],[6,7,6,7]] 

    def test_embed(self):
        driver = redisdriver.GrphclusRedisDriver('elyzee_small_temp_edges.json', send_edge=False)
        e = driver.embed('Grphclus est un outil massif')
        self.assertEqual(e[1], 1)

    def test_add_edge(self):
        driver = redisdriver.GrphclusRedisDriver('elyzee_small_temp_edges.json', send_edge=False)
        for ta in self.twitterActivities:
            driver.add_edge(ta)
        self.assertEqual(len(driver.graph.nodes),7)
        sum_weights = sum([ driver.graph.edges[e]['weight'] for e in driver.graph.edges ]) 
        self.assertEqual(sum_weights,len(self.twitterActivities))

    def test_get_centroids(self):
        driver = redisdriver.GrphclusRedisDriver('elyzee_small_temp_edges.json', send_edge=False)
        for ta in self.twitterActivities:
            driver.add_edge(ta)
        idx_cols_selected, com_embed = driver.get_centroids(self.communities)
        # let's say the selected key words should at least appear in the tweets
        self.assertEqual(len([1 for i in idx_cols_selected if driver.number_word_occurences(i) > 0 ]), 10)

    def test_remap_centroid(self)
        remapping = redisdriver.remap_centroids(centroids, centroids_past)
        self.assertEquel(remapping, [[6, 7, 6, 7], [4, 5, 4, 5], [1, 2, 1, 2]])

    def test_get_centroid(self):
        driver = redisdriver.GrphclusRedisDriver()
        result_id = driver.put_result(self.result)
        actual = driver.get_result(result_id)
        self.assertEqual(self.result, actual)

    def test_get_all(self):
        driver = MemDriver()
        id1 = driver.put_result(self.result)
        id2 = driver.put_result(self.result)
        results = driver.get_results()
        self.assertEqual(2, len(results))
        self.assertLess(results[id1]['created'], results[id2]['created'])

    def test_get_start(self):
        driver = MemDriver()
        id1 = driver.put_result(self.result)
        time.sleep(.5)
        id2 = driver.put_result(self.result)
        results = driver.get_results(datetime.now() - timedelta(seconds=.3))
        self.assertEqual(1, len(results))
        self.assertIn(id2, results)
        self.assertEqual('test', results[id2]['meta'])
