import copy
import string, time
import numpy as np
import json
from datetime import datetime
from secrets import choice
from threading import Lock
import threading
import networkx as nx
from scipy.spatial import distance
from munkres import Munkres
from scipy import stats as s
import pickle
import math

class Fake_redis_driver_naval:
    """get some data, push then sequentially to grphclus, and read the result in the redis database which the grphclus storage"""

    def __init__(self, pickle_containing_graph_and_coms, send_edge=True):
        """
        Create a new MemDriver instance
        """

        data = pickle.load(open(pickle_containing_graph_and_coms, 'rb')) 
        self.graph = data['graph']
        self.communities = data['communities']
        self.com_id = -1

        self.time_idx = 300
        self.dates = sorted(self.communities.keys()) #, key = lambda t: time.strptime(t, '%a %b %d %H:%M:%S +0000 %Y')) 
        self.last_date = self.dates[self.time_idx]
        self.level = 1
        self.time_traveller_mode = False
        self.present = 0

    def put_result(self, result):
        """
        no implementation, because the redis database is filled by grphclus
        """
        return {}

    def set_level(self, level):
        self.com_id = -1
        self.level = int(level)
        community_tree = self.communities[self.last_date]['community_tree']
        num_of_communities = len([ n for n in community_tree.nodes if community_tree.nodes[n]['level'] == self.level ])
        levels = set([community_tree.nodes[n]['level'] for n in community_tree.nodes ])
        return len(levels), self.level, num_of_communities, self.com_id

    def get_num_levels(self):
        community_tree = self.communities[self.last_date]['community_tree']
        levels = set([community_tree.nodes[n]['level'] for n in community_tree.nodes ])
        num_of_levels = len(levels) - 1
        num_of_com = len([ n for n in community_tree.nodes if community_tree.nodes[n]['level'] == self.level ]) 
        print("last date", self.last_date, 'index', self.time_idx, num_of_levels, self.level, num_of_com, self.com_id)
        return num_of_levels, self.level, num_of_com, self.com_id

    def set_date(self, date):
        date = int(date)
        if not self.time_traveller_mode:
            self.present = self.time_idx # recall when is the present to go back
            self.time_traveller_mode = True
        print('traveled to', self.dates[date])
        self.time_idx = date
        if self.time_idx >= self.present:
            print('back to present or even the future')
            self.time_traveller_mode = False # back to normal life
        return self.get_result(0)

    def put_result_id(self, result, result_id):
        """
        no implementation, the redis database is filled by grphclus
        """
        return {}
 
    def get_community_detail(self):
        pass


    def get_result(self, result_id):
        """
        Ignoring the result_id actually, just read what is in the redis database 
        """
        self.last_date = self.dates[self.time_idx]
        community_tree = self.communities[self.last_date]['community_tree']
        communities = aggregate_childrens(community_tree, self.level)
        graph = {"nodes": [], "links": []}
        nodes = [ {'id':n, 'value':int(1+math.log(len(communities[n])))} for n in community_tree.nodes if community_tree.nodes[n]['level'] == self.level ]
        links = []
        for i, n in enumerate(nodes):
            n1 = n['id']
            for j in range(i+1,len(nodes)):
                n2 = nodes[j]['id']
                if (n1, n2) in community_tree.edges:
                    if 'weight' not in community_tree.edges[(n1,n2)]:
                        print(n1,n2)
                        continue
                    weight = community_tree.edges[(n1,n2)]['weight']
                    weight = min(100, math.log(weight))
                    if weight == 0:
                        continue
                    links.append({'id':'_'.join(sorted([str(n1),str(n2)])),  "source": n1, "target": n2, "value": weight} )

        if self.time_idx < len(self.dates) - 1 and not self.time_traveller_mode:
            self.time_idx += 1        
        for n in nodes:
          n['id'] = str(n['id'])
        graph['nodes'] = nodes
        graph['links'] = links
        print(graph)
        print([e['value'] for e in links])
        return graph 

    """
    def get_result(self, result_id):
        self.time_idx += 1
        nnodes = self.time_idx % 10 + 1
        nodes = [{"id":i, "name":i} for i in range(nnodes) ]
        links = [ {"id": '_'.join(sorted([str(n),str(n+1)])), "source":n, "target":n+1 } for n in range(nnodes-1)]
        result = {"links":links, "nodes":nodes }
        print(result)
        return result
    """

    def detail_community(self, com_id):
        self.com_id = int(com_id)
        print('setting the detail on community',self.com_id)
        return self.get_result(0) 

    def get_results(self, start=None):
        return {
            k: _make_meta(v)
            for k, v in self.results.items()
            if start is None or v['created'] > start
        }
        
    def get_last_date(self):
        return self.last_date

    def how_is_the_graph(self):
        print('number of nodes', len(self.graph.nodes))
        print('number of edges', len(self.graph.edges))

def remap_centroids(centroids, last_centroids):
    """
    remap which hungarian method
    """
    m = np.zeros((len(centroids),len(last_centroids)))
    ks = list(centroids.keys())
    for i, k in enumerate(ks):
      for j in range(len(last_centroids)): #enumerate(last_ks):
        c1 = centroids[k]
        c2 = last_centroids[j]
        m[i,j] = distance.euclidean(np.array(c1), np.array(c2))
    mu = Munkres()
    if m.shape[0] > m.shape[1]:
      indices = mu.compute(copy.copy(m.transpose()))
      indices = dict([(j,i) for (i,j) in indices])
    else:
      indices = dict(mu.compute(copy.copy(m)))
    ks_rearranged = [[]]*len(centroids)
    to_add = set(range(len(ks))) # all of them should arrive in ks_rearranged
    # add the ones which has been mapped by the hungarian algorithm
    for i in range(len(centroids)):
      if i in indices and indices[i]<len(centroids):
        ks_rearranged[indices[i]] = ks[i]
        to_add.remove(i)
    """
    print(centroids)
    print('last',last_centroids)
    print(ks_rearranged)
    print('indices', indices)
    """
    # add the remaining ones
    for i in range(len(centroids)):
      if not ks_rearranged[i]: # if this one is empty #len(ks_rearranged[i]) == 0:
        ks_rearranged[i] = ks[to_add.pop()]
    return ks_rearranged



def aggregate_childrens(community_tree, level): 
    communities = {} 
    if level == 0: 
        return {} 
    com_id_this_level = [ n for n in community_tree.nodes if community_tree.nodes[n]['level'] == level ] 
    for n in com_id_this_level: 
        communities[n] = get_all_leaves(community_tree, n) 
    return communities  
 
def get_childrens(G, node_id): 
    return [ n for n in G.neighbors(node_id) if G.nodes[n]['level'] < G.nodes[node_id]['level'] ] 
 
def get_all_leaves(community_tree, n): 
    leaves = [] 
    childrens = get_childrens(community_tree, n) 
    if len(childrens) == 0: 
        leaves.append(n) 
    for child in get_childrens(community_tree, n): 
        leaves += get_all_leaves(community_tree, child) 
    return leaves

def hashy(node):
    int(node)
    hashy = node // 100
    key = hashy * 100 - node
    return hashy, key

def unhash(hashy, key):
    return int(hashy) * 100 - int(key)


def compute_entropy(data):
    """
    data is a matrix number_of_key_words X number_of_communities
    data[i,j] : how many times the key_word i appears in the community j
    """
    row_normalise(data)
    entropies = sum(data*log(data))
    return entropies

def load_data(f):
    d = json.load(open(f))
    return d
    
def _make_record(result):
    return {
        'result': result,
        'created': datetime.now(),
        'meta': result.get('meta')
    }

def _make_meta(record):
    return {k: v for k, v in record.items() if k != 'result'}
