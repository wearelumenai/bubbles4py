import copy
import string, time
import numpy as np
import json
from datetime import datetime
from secrets import choice
from threading import Lock
import redis
import pika
import threading
import networkx as nx
from scipy.spatial import distance
from munkres import Munkres

url = "amqp://mclouvain:mcl@localhost:5672/"
json_file_containing_tweet = '/home/paul/programmation/lumenai/bubbles4py/elyzee_small_test_graph.json'
redis_port = 26611


topics = { 'colere': ['menace', 'attentat', 'mauvais','imposture', 'erreur','assez','guerre' 'violence', 'attaquer', 'attentat', 'police', 'escroquerie', 'manifestation', 'mensonge', 'mentir', 'systeme'], 'société': [ 'Retraités', 'islamistes', 'riches', 'supporter', 'exprimer', 'islamiste', 'europe', 'système'], 'economy': ['finance','économie', 'crise', 'entreprises', 'entreprise', 'bulle', 'libéral', 'classes', 'agriculture', 'chômeur', 'travail', 'euro', 'argent', 'milliard', 'dette'], 'macron': ['marche','emmanuel', 'macron', 'manuel'], 'ps': ['hollande', 'gauche', 'valls', 'benoît', 'socialiste'], 'republicains': ['fillon', 'sarkozy', 'juppé', 'penelope', 'droite', 'nicolas',  'pénélope', 'alain', 'françois'], 'insoumis': ['mélenchon', 'insoumis', 'luc', 'jean' ], 'rassembl.': ['marine', 'france'], 'positif' : ['soutien', 'gagn', 'avenir', 'soutenir', 'premier', 'bravo', 'allez', 'enfin', 'chance', 'rall', 'solution', 'mobilisation',  'confiance'] }
key_topics = list(topics.keys())

class GrphclusRedisDriver:
    """get some data, push then sequentially to grphclus, and read the result in the redis database which the grphclus storage"""

    def __init__(self, json_file_containing_tweet, send_edge=True):
        """
        Create a new MemDriver instance
        """
        
        self.port = redis_port
        data = load_data(json_file_containing_tweet)
        self.common_words = data['common_words']
        self.graph = nx.Graph() # will store all the edges sent to grphclus, and is used to compute statistics about the data sent when doing the bubble visualisation 
        self.last_centroids = []
        if send_edge:
            x = threading.Thread(target=self.send_tweets, args=(data['edges'],), daemon=True)
            x.start()
        self._mu = Lock()
        """
        r = redis.Redis(host='localhost', port=26611, db=0)
        self.results = {}
        """

    def put_result(self, result):
        """
        no implementation, because the redis database is filled by grphclus
        """
        return {}


    def put_result_id(self, result, result_id):
        """
        no implementation, because the redis database is filled by grphclus
        """
        return {}
 
    def get_result(self, result_id, level=1):
        """
        Ignoring the result_id actually, just read what is in the redis database 
        """
        metadataDbID, graphDbID, CommunityDbID, mappingDbID = (level - 1)*4 + 1,  (level - 1)*4 + 2, (level - 1)*4 + 3, (level - 1)*4 + 4
        rmeta = redis.Redis(host='localhost', port=redis_port, db=metadataDbID)
        node2twitterID = dict( [ (rmeta.get(k),k) for k in rmeta.keys('*') if k.isdigit() ])
        rcom = redis.Redis(host='localhost', port=redis_port, db=CommunityDbID)
        # there is an interesting fact here, the set of keys between the two calls ".keys("*")" may be different, because, the some new edges have been added to the redis database meanwhile
        communities = dict([ (com_id,  set([ node2twitterID[x] for x in rcom.smembers(com_id) if x in node2twitterID ]) ) for com_id in rcom.keys('*') ]) 
        columns, centroids = self.get_centroids2(communities)
        if len(self.last_centroids) != 0:
          ordering = remap_centroids(centroids, self.last_centroids)
        else:
          ordering = sorted(centroids.keys())
        self.last_centroids = centroids
        result = {}
        result['centers'] = [ centroids[k] for k in ordering ]
        result['counts'] = [ len(communities[k]) for k in ordering ]
        result['columns'] = columns 
        print('sending results')
        print('number of communities',len(communities))
        print('the selected keywords:', result['columns'])
        print('the centroids:', result['centers'])
        with self._mu:
            return result #self.results[result_id]['result']

    def get_results(self, start=None):
        return {
            k: _make_meta(v)
            for k, v in self.results.items()
            if start is None or v['created'] > start
        }

    def embed_topic(self, txt):
      tweet_embed = np.zeros(len(key_topics))
      for w in txt.split(' '):
        for i in range(len(key_topics)):
          words = topics[key_topics[i]]
          for wt in words:
            if wt in w:
              tweet_embed[i] = 1
              break   
      return tweet_embed        

    def embed(self, txt):
      """
      return binary vector where tweet_embed[i] = 1 if the txt contain the key word number i
      probably not the most semantic embedding, but at least, it is interpretable
      """
      tweet_embed = np.zeros(len(self.common_words))
      for w in txt.split(' '):
        if w in self.common_words:
          tweet_embed[self.common_words.index(w)] = 1
      return tweet_embed

    def add_edge(self, twitterActivity):
        # getting the tweet embedding
        tweet_embed = self.embed_topic(twitterActivity['txt'])
        author = twitterActivity['source'].encode('UTF-8')
        connection = twitterActivity['target'].encode('UTF-8')
        if (connection, author) in self.graph.edges:
            self.graph.edges[(connection, author)]['weight'] += 1
        else:
            self.graph.add_edge(connection, author, created_at=twitterActivity['created_at'])
            self.graph.edges[(connection, author)]['weight'] = 1

        # updating the embedding for the node author
        if 'features' not in self.graph.nodes[author]:
            self.graph.nodes[author]['features'] = tweet_embed
        else:
            self.graph.nodes[author]['features'] += tweet_embed

    def send_tweets(self, edges):
        # sort the edges
        edges = sorted(edges, key = lambda t: time.strptime(t['created_at'], '%a %b %d %H:%M:%S +0000 %Y'))

        # create the connection for rabbitmq
        parameters = pika.URLParameters(url)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='Edges', durable=True) # hoping that the config in Grphclus has named its queue as Edges
        # sending the edges to grphclus
        for i, twitter_activity in enumerate(edges):
            self.add_edge(twitter_activity)
            start = twitter_activity['source']
            end = twitter_activity['target']
            body = '[[Edges]]\nstart = "'+start+'"\nweight = 1.0\nend = "'+end+'"\nreltype = "type"\ncontent = "content"\ntimestamp = 1576794545000' # yeah content and timestamp are not used
            return_mess =  channel.basic_publish(exchange='', routing_key='Edges', body=body, mandatory=True)
            # add the edge sent to the driver Graph.
            if i%1000 == 0:
                print('sent', i, 'edges over',len(edges))            
                print("Sent body", return_mess)
                time.sleep(2) # just to go slowly, I have a small computer 

    def get_centroids2(self, communities):
        """
        compute some centroids
        """
        com_embed = {}
        c_keys = list(communities.keys())
        com_embed = np.zeros((len(key_topics), len(c_keys)))
        self.how_is_the_graph()
        print(len(communities),' communities:', [ (k,len(communities[k])) for k in c_keys ])
        print('from a number of node of : ', sum([len(communities[k]) for k in c_keys ]))
        for i, k in enumerate(c_keys):
          nodes = communities[k]
          com_embed[:,i] = np.sum([self.graph.nodes[n]['features'] for n in nodes if  'features' in self.graph.nodes[n] ], axis=0)
        """
        com_embed[com_embed<np.median(com_embed[com_embed!=0])*0.25] = 0 # removing low values, like values which are lower than 0.25 * median_value 
        com_embed += 0.00000001
        com_embed = com_embed / np.sum(com_embed,axis=1).reshape(-1,1) # row normalise
        entropies = -np.sum(com_embed * np.log(com_embed), axis=1)
        idx_lowest_entropies = np.argsort(entropies)[:10]
        # because you cannot pass numpy array to bubble, I convert to list
        """
        centroids = {} 
        for i, k in enumerate(c_keys):
            centroid = []
            for j in range(len(key_topics)): #idx_lowest_entropies:
              centroid.append(com_embed[j,i])
            centroids[k] = centroid
        return key_topics, centroids 


    def get_centroids(self, communities):
        """
        compute some centroids
        """
        com_embed = {}
        c_keys = list(communities.keys())
        com_embed = np.zeros((len(self.common_words), len(c_keys))) 
        self.how_is_the_graph()
        print('communities:', [ (k,len(communities[k])) for k in c_keys ])
        print('in total: ', sum([len(communities[k]) for k in c_keys ]))
        for i, k in enumerate(c_keys):
          nodes = communities[k]
          com_embed[:,i] = np.sum([self.graph.nodes[n]['features'] for n in nodes if  'features' in self.graph.nodes[n] ], axis=0)
        com_embed[com_embed<np.median(com_embed[com_embed!=0])*0.25] = 0 # removing low values, like values which are lower than 0.25 * median_value 
        com_embed += 0.00000001
        com_embed = com_embed / np.sum(com_embed,axis=1).reshape(-1,1) # row normalise
        entropies = -np.sum(com_embed * np.log(com_embed), axis=1)
        idx_lowest_entropies = np.argsort(entropies)[:10]
        # because you cannot pass numpy array to bubble, I convert to list
        centroids = {} 
        for i, k in enumerate(c_keys):
            centroid = []
            for j in idx_lowest_entropies:
              value = round(com_embed[j,i]*10000)/100
              centroid.append(value)
            centroids[k] = centroid
        return idx_lowest_entropies, centroids 

    def number_word_occurences(self, i):
        return sum([self.graph.nodes[n]['features'][i] for n in self.graph.nodes if 'features' in self.graph.nodes[n] ])

    def how_is_the_graph(self):
        print('number of nodes', len(self.graph.nodes))
        print('number of edges', len(self.graph.edges))

def remap_centroids(centroids, last_centroids):
    m = np.zeros((len(centroids),len(last_centroids)))
    ks = list(centroids.keys())
    last_ks = sorted(last_centroids.keys())
    for i, k in enumerate(ks):
      for j, last_k in enumerate(last_ks):
        c1 = centroids[k]
        c2 = last_centroids[last_k]
        m[i,j] = distance.euclidean(np.array(c1), np.array(c2))
    mu = Munkres()
    if m.shape[0] > m.shape[1]:
      indices = mu.compute(copy.copy(m.transpose()))
      indices = dict([(j,i) for (i,j) in indices])
    else:
      indices = dict(mu.compute(copy.copy(m)))
    ks_rearranged = [[]]*len(centroids)
    to_add = set(range(len(ks)))
    for i in range(len(centroids)):
      if i in indices and indices[i]<len(centroids):
        ks_rearranged[indices[i]] = ks[i]
        to_add.remove(i)
    for i in range(len(centroids)):
      if len(ks_rearranged[i]) == 0:
        ks_rearranged[i] = ks[to_add.pop()]
    return ks_rearranged


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
