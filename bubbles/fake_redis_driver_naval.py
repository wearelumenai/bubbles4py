from scipy.optimize import curve_fit
import random
import string, time
import numpy as np
import json
from datetime import datetime
from secrets import choice
from threading import Lock
import threading
import networkx as nx
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
        self.colors = {}
        self.last_level = -1
        self.offset = 0
        self.time_idx = self.offset
        self.dates = sorted(self.communities.keys()) #, key = lambda t: time.strptime(t, '%a %b %d %H:%M:%S +0000 %Y')) 
        self.level = 1
        self.stop_time= False
        self.switch_com_nodeid = True

    def switch_stop_time(self):
        self.stop_time = False if self.stop_time else True

    def put_result(self, result):
        """
        no implementation, because the redis database is filled by grphclus
        """
        return {}

    def set_level(self, level):
        self.com_id = -1
        self.last_level = self.level
        self.level = int(level)
        community_tree = self.communities[self.dates[self.time_idx]]['community_tree']
        num_of_communities = len([ n for n in community_tree.nodes if community_tree.nodes[n]['level'] == self.level ])
        levels = list(set([community_tree.nodes[n]['level'] for n in community_tree.nodes ]))
        if len(levels) > 1:
            levels.pop()
        num_of_coms = self.num_of_coms(community_tree, len(levels))
        return len(levels), self.level, num_of_coms, self.com_id

    def switch_com_nodeid_func(self):
        self.switch_com_nodeid = not self.switch_com_nodeid

    def num_of_coms(self, community_tree, num_of_levels):

        def num_of_com(level):
            return len([ n for n in community_tree.nodes if community_tree.nodes[n]['level'] == level ])

        return [
            num_of_com(level) for level in range(num_of_levels)
        ]

    def get_num_levels(self):
        community_tree = self.communities[self.dates[self.time_idx]]['community_tree']
        levels = list(set([community_tree.nodes[n]['level'] for n in community_tree.nodes ]))
        if len(levels) > 1: # assuming the last one is useless because it does not have edges
            levels.pop()
        num_of_levels = len(levels)

        num_of_coms = self.num_of_coms(community_tree, num_of_levels)

        print("last date", self.dates[self.time_idx], 'index', self.time_idx, num_of_levels, self.level, num_of_coms, self.com_id)
        return num_of_levels, self.level, num_of_coms, self.com_id

    def set_date(self, date):
        date = int(date) +  self.offset 
        print('traveled to', self.dates[date])
        self.time_idx = date
        return self.get_result(0)

    def put_result_id(self, result, result_id):
        """
        no implementation, the redis database is filled by grphclus
        """
        return {}
 
    def get_community_detail(self):
        pass

    def get_node_color(self, nodeid):
        if nodeid not in self.colors:
            self.colors[nodeid] = '%06x' % random.randrange(16**6)
        return self.colors[nodeid]

    def get_curve(self, time_idx=None, level=None):
        if time_idx is None:
            time_idx = self.time_idx
        time_idx = min(time_idx, len(self.dates))
        values = []
        if level is None:
            level = self.level
        #level = 3
        for i in range(len(self.dates)): #time_idx)
            community_tree = self.communities[self.dates[i]]['community_tree']
            com_id_this_level = [ n for n in community_tree.nodes if community_tree.nodes[n]['level'] == level ]
            values.append({'date': self.dates[i], 'value': len(com_id_this_level)})
        #for i in range(len(values)):
        #    values[i] = sum(values[i-2:i+2])
        return values

    def get_community_activities(self, communities):
        community_activities = {}
        for (com_id, nodes) in communities.items():
            activities_this_com = []
            for n in nodes:
                activities_this_node = [ self.graph.edges[e]['created_at'] for e in self.graph.edges(int(float(n))) ]
                if len(activities_this_node) == 0:
                    print('no activity for node', n,com_id,self.level)
                    last_activity_this_node = 0
                else:
                    last_activity_this_node = max(activities_this_node)
                activities_this_com.append(last_activity_this_node)
            activity_this_com = np.quantile(activities_this_com, 0.8)
            community_activities[com_id] = activity_this_com
        community_activities = self.squash_with_sigmoid(community_activities)
        return community_activities


    def squash_with_sigmoid(self, community_activities):
        values = list(community_activities.values())
        min_x, max_x, middle_x = np.min(values), np.max(values), np.median(values)
        """
        values = [ max(0.2, (v - min_x) / (max_x - min_x)) for v in values]
        ydata = np.array([0.2, 0.5, 1])
        xdata = np.array([min_x, middle_x, max_x])
        popt, pcov = curve_fit(self.sigmoid, xdata, ydata)
        """
        for (com_id, activity) in community_activities.items():
            community_activities[com_id] = max(0.2, (activity - min_x) / (max_x - min_x))  #self.sigmoid(activity, *popt)
        return community_activities

    def sigmoid(self, x, x0, k):
        y = 1 / (1+ np.exp(-k*(x-x0)))
        return y


    def get_result(self, result_id):
        """
        Ignoring the result_id actually, just read what is in the redis database 
        """
        print(self.time_idx, len(self.dates))
        last_date = self.dates[self.time_idx]
        community_tree = self.communities[last_date]['community_tree']
        communities = aggregate_childrens(community_tree, self.level)
        community_activities = self.get_community_activities(communities)
        graph = {"nodes": [], "links": []}
        nodes = [ {'id':n, 'value':int(1+math.log(len(communities[n]))), 'opacity': community_activities[n] } for n in community_tree.nodes if community_tree.nodes[n]['level'] == self.level ]
        print('level', self.level, 'last level', self.last_level, 'time traveller', self.stop_time)
        for n in nodes:
            if (not self.switch_com_nodeid) or self.last_level == self.level -1: # each node get it's own color (special case if you were in community view mode and jump to the higher level, in order to preserve color consistency between two subsequent levels
                n['color'] = self.get_node_color(n['id'])
            else: # each node will have the color of its parent
                child_level = community_tree.nodes[n['id']]['level']
                color = None
                for potential_parent in community_tree.neighbors(n['id']): 
                    if community_tree.nodes[potential_parent]['level'] == child_level + 1:
                        color = self.get_node_color(potential_parent)
                        break
                if color is None: # this node did not have any parent, (maybe it was at the community top level of the hierarchy)
                    color = self.get_node_color(n['id'])
                n['color'] = color
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

        if self.time_idx < len(self.dates) - 1 and not self.stop_time:
            self.time_idx += 1        
        for n in nodes:
          n['id'] = str(n['id'])
        graph['nodes'] = nodes
        graph['links'] = links
        graph['com_nodeid'] = self.switch_com_nodeid
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
        return self.dates[self.time_idx] 

    def how_is_the_graph(self):
        print('number of nodes', len(self.graph.nodes))
        print('number of edges', len(self.graph.edges))


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
