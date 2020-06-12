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

party_to_cat = {'em': 0,
 'indetermined': 1,
 'ps': 2,
 'lr': 3,
 'fn': 4,
 'fi': 5,
 'multi_affiliations': 6}

topics = { 'colere': ['menace', 'attentat', 'mauvais','imposture', 'erreur','assez','guerre' 'violence', 'attaquer', 'attentat', 'police', 'escroquerie', 'manifestation', 'mensonge', 'mentir', 'systeme'], 'société': [ 'Retraités', 'islamistes', 'riches', 'supporter', 'exprimer', 'islamiste', 'europe', 'système'], 'economy': ['finance','économie', 'crise', 'entreprises', 'entreprise', 'bulle', 'libéral', 'classes', 'agriculture', 'chômeur', 'travail', 'euro', 'argent', 'milliard', 'dette'], 'macron': ['marche','emmanuel', 'macron', 'manuel'], 'ps': ['hollande', 'gauche', 'valls', 'benoît', 'socialiste'], 'republicains': ['fillon', 'sarkozy', 'juppé', 'penelope', 'droite', 'nicolas',  'pénélope', 'alain', 'françois'], 'insoumis': ['mélenchon', 'insoumis', 'luc', 'jean' ], 'rassembl.': ['marine', 'france'], 'positif' : ['soutien', 'gagn', 'avenir', 'soutenir', 'premier', 'bravo', 'allez', 'enfin', 'chance', 'rall', 'solution', 'mobilisation',  'confiance'] }
key_topics = list(topics.keys())

class Fake_redis_driver:
    """get some data, push then sequentially to grphclus, and read the result in the redis database which the grphclus storage"""

    def __init__(self, pickle_containing_graph_and_coms, send_edge=True):
        """
        Create a new MemDriver instance
        """
        
        data = pickle.load(open(pickle_containing_graph_and_coms, 'rb')) 
        self.graph = data['graph']
        self.communities = data['communities']
        self.com_id = -1

        self.time_idx = 1
        self.dates = sorted(self.communities.keys(), key = lambda t: time.strptime(t, '%a %b %d %H:%M:%S +0000 %Y')) 
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
        communities = self.communities[self.last_date][self.level]
        return len(self.communities[self.last_date]), self.level, len(communities), self.com_id

    def set_date(self, date):
        date = int(date)
        if not self.time_traveller_mode:
            self.present = self.time_idx # recall when is the present to go back
            self.time_traveller_mode = True
        print('traveled to', self.dates[date])
        self.time_idx = date
        if self.time_idx == self.present:
            print('back to present')
            self.time_traveller_mode = False # back to normal life
        return self.get_result(0)

    def put_result_id(self, result, result_id):
        """
        no implementation, the redis database is filled by grphclus
        """
        return {}
 
    def get_community_detail(self):
        pass

    def communities_to_graph(self, communities):
        graph = {"nodes": [], "links": []}
        for k in communities:
            graph["nodes"].append({"id":k, "name":k})
        for k1, v1 in communities.items():
            for k2, v2 in communities.items():
              graph['links'] = []
        return graph

    def get_result(self, result_id):
        """
        Ignoring the result_id actually, just read what is in the redis database 
        """
        self.last_date = self.dates[self.time_idx]
        """
        print('time',self.time_idx)
        if self.com_id == -1 or self.level == 1:
            if self.level not in self.communities[self.last_date]:
                if self.time_idx < len(self.dates) - 1:
                    self.time_idx += 1
                return {'centers': [], 'counts': [], 'columns': []}
            communities = self.communities[self.last_date][self.level]

        else:
            communities = self.get_community_detail()
        """
        if self.time_idx < len(self.dates) - 1 and not self.time_traveller_mode:
            self.time_idx += 1        
        self.time_idx += 1
        result = json.load(open('/home/paul/programmation/lumenai/bubbles4py/examples/data_network.json'))
        print("returning", result)
        return result #self.results[result_id]['result']


    def get_result_centr(self, result_id):
        """
        Ignoring the result_id actually, just read what is in the redis database 
        """
        self.last_date = self.dates[self.time_idx]
        print('time',self.time_idx)
        if self.com_id == -1 or self.level == 1:
            if self.level not in self.communities[self.last_date]:
                if self.time_idx < len(self.dates) - 1:
                    self.time_idx += 1
                return {'centers': [], 'counts': [], 'columns': []}
            communities = self.communities[self.last_date][self.level]

        else:
            communities = self.get_community_detail()
        if self.time_idx < len(self.dates) - 1 and not self.time_traveller_mode:
            self.time_idx += 1        
        self.time_idx += 1
        result = {}
        result['centers'] = communities['centers'] 
        result['counts'] = [ len(communities['communities'][k]) for k in communities['ordering'] ]
        result['columns'] = communities['columns']
        print('sending results')
        print('number of communities',len(communities), 'time',self.last_date)
        print('the selected keywords:', result['columns'])
        print('the centroids:', result['centers'][0])
        return result #self.results[result_id]['result']

    def get_num_levels(self):
        num_of_levels = len(self.communities[self.last_date])
        num_of_com = len(self.communities[self.last_date][self.level]['communities'])
        print("last date", self.last_date, 'index', self.time_idx, num_of_levels, self.level, num_of_com, self.com_id)
        return num_of_levels, self.level, num_of_com, self.com_id

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
