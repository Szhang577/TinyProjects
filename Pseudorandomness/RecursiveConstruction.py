# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 13:42:31 2020

@author: lnajt
"""

import itertools
import random
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import os
import secrets
import sympy
import copy
from sympy import nextprime

'''
Things to experiment with:
    
    1) Expander Steps on Hashes
    2) Random shifts
    3) Edge Replacement Gadgets
    
Ways to validate experiments:
    
    1) Whether min-path is unique. ()
'''

def viz(graph):
    pos = {x : graph.nodes[x]["pos"] for x in graph.nodes()}
    col = [graph.nodes[x]["weight"] for x in graph.nodes()]
    nx.draw(graph, pos, node_color =col, node_size = 100, width =.5, cmap=plt.get_cmap('hot'))

def binary_strings(m):
    #Is an iterator that gives all binary strings of length m
    i = 0
    while i < 2**m:
        pre_padded = bin(i)[2:]
        string = pre_padded.zfill(m)
        yield (string )
        i += 1
        
def path_to_edge(path):
    i = 0
    edge_list = []
    while i < len(path) -1: 

        edge_list.append( ( path[i], path[i+1]))
        i += 1
    return edge_list

def branching_tree(l):
    #Creates a doubled layered branching tree with l layers
    d = 2**l
    print("not written yet")
    layered_nodes = itertools.product(range(n), range(d + 1))
    
    graph = nx.DiGraph()
    graph.add_nodes_from(layered_nodes)
    
    
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        
    graph.graph["num_layers"] = l
    graph.graph["width"] = n
    for i in range(d):
        for k in range(n):
            if i == 0:
                graph.add_edge( (0,0) , (k,1))
            if i > 0 and i < d - 1:
                graph.add_edge( ( k,i) , (k,i+1))
            if i == d - 1:
                graph.add_edge( (k,i), (0, d))
        
                
    i = 0
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        graph.nodes[x]["label"] = i
        i += 1
        graph.nodes[x]["weight"] = 0
        
    #viz(graph)
    graph.graph["s"] = (0,0)
    graph.graph["t"] = (0,d)    
    return graph
    

def disjoint_paths(n = 5,l = 3):
    d = 2**l
    
    layered_nodes = itertools.product(range(n), range(d + 1))
    
    graph = nx.DiGraph()
    graph.add_nodes_from(layered_nodes)
    
    
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        
    graph.graph["num_layers"] = l
    graph.graph["width"] = n
    for i in range(d):
        for k in range(n):
            if i == 0:
                graph.add_edge( (0,0) , (k,1))
            if i > 0 and i < d - 1:
                graph.add_edge( ( k,i) , (k,i+1))
            if i == d - 1:
                graph.add_edge( (k,i), (0, d))
        
                
    i = 0
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        graph.nodes[x]["label"] = i
        i += 1
        graph.nodes[x]["weight"] = 0
        
    #viz(graph)
    graph.graph["s"] = (0,0)
    graph.graph["t"] = (0,d)
    return graph
    

def random_subset_iterator(collection, r):
    #Returns a random subset of size r of collection on each call
    while True:
        subset = random.choices(collection, k = r)
        yield subset
    
    
def generate_unions_of_paths(n = 4, l= 3, r = 3, random = False):
    graph = complete_layered_digraph(n, l)
    paths = nx.all_simple_paths(graph, graph.graph["s"], graph.graph["t"])
    '''
    We could do a backtraking tree, where we put edges either into J (the edge set
    ), or its complement. Checking whether such an assignment can be completed amounts to verifying
    that the complement is not a cut of the layered complete digraph, so we can delete and 
    ask networkx for connectivity. In some cases it may be that certain sets of edges
    will necessarily be included, but maybe sufficiently efficient to find them on later levels of the tree.
    Of course there are still a lot of connected layered digraphs. ... actually most likely the ones that are unions of paths are most interesting, since we want there to be many paths before we set weights.
    '''
    paths_as_edge_sets = [ set(path_to_edge(path)) for path in paths]
    merged = []
    num_paths = len(paths_as_edge_sets)
    
    if random == False:
        path_iterator = itertools.combinations(paths_as_edge_sets, r)
    else:
        path_iterator = random_subset_iterator(paths_as_edge_sets, r)
    
    for path_collection in path_iterator:
        merge = set()
        for path in path_collection:
            merge = merge | path
        subgraph = nx.DiGraph(nx.edge_subgraph(graph, list(merge)))
        for x in graph.nodes():
            if x not in subgraph.nodes():
                subgraph.add_node(x)
        t = 0
        for x in subgraph.nodes():
            #print(x)
            subgraph.nodes[x]["pos"] = np.array([x[0], x[1]])
            subgraph.nodes[x]["label"] = t
            t += 1
            subgraph.nodes[x]["weight"] = 0
            
        
        yield subgraph
                    
def generate_all_layered_digraphs(n = 4, l = 3):
    #To find some examples where a single hash function doesn't work, we'll 
    #Iterate through all examples.
    
    d = 2**l
    
    layered_nodes = itertools.product(range(n), range(d + 1))
    
    graph = nx.DiGraph()
    graph.add_nodes_from(layered_nodes)
    
    
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        
    #Iterate through binary strings corresponding to edges
        
    def indexing_sub(i,k,n):
        #Maps [m] x [n] to [mn]
        
        return i * n + k
        
    def indexing_function(i,k,j,n):
        #A bijection between [d]x[n]x[n] and [d*n^2]
        
        #[n]x[n] -> [n^2] : (k,j) -> ( k -1)*n + j

        a = indexing_sub(k,j,n)
        
        #[d]x[n^2] -> [dn^2] (i,a) -> (i - 1) * n^2 + a
        
        return indexing_sub(i, a, n**2)
        
    for adjacency_matrix in binary_strings(d*(n**2)):
        graph = nx.DiGraph()
        layered_nodes = itertools.product(range(n), range(d + 1))
        graph.add_nodes_from(layered_nodes)
        
        
        for x in graph.nodes():
            #print(x)
            graph.nodes[x]["pos"] = np.array([x[0], x[1]])
            
        for i in range(d):
            for k in range(n):
                for j in range(n):
                    if adjacency_matrix[indexing_function(i,k,j,n)] == '1':
                        #print(indexing_function(i, k, j, n))
                        graph.add_edge( (k,i), (j, i+1))
                        
        t = 0
        for x in graph.nodes():
            #print(x)
            graph.nodes[x]["pos"] = np.array([x[0], x[1]])
            graph.nodes[x]["label"] = t
            t += 1
            graph.nodes[x]["weight"] = 0
            
        #viz(graph)
        graph.graph["num_layers"] = l
        graph.graph["width"] = n
        graph.graph["s"] = (0,0)
        graph.graph["t"] = (0,d)         
        viz(graph)
                        
        yield graph
        

def create_layered_digraph(n = 4, l = 3, density = .5):

    d = 2**l
    
    layered_nodes = itertools.product(range(n), range(d + 1))
    
    graph = nx.DiGraph()
    graph.add_nodes_from(layered_nodes)
    
    
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        
    graph.graph["num_layers"] = l
    graph.graph["width"] = n
    for l in range(d):
        for k in range(n):
            for p in range(int(density*n)):
                u = random.choice(list(range(n)))
                graph.add_edge( (k,l), (u, l+1))
                
    i = 0
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        graph.nodes[x]["label"] = i
        i += 1
        graph.nodes[x]["weight"] = 0
        
    #viz(graph)
    graph.graph["s"] = (0,0)
    graph.graph["t"] = (0,d)
    return graph 

def complete_layered_digraph(n = 4, l = 3):
    d = 2**l
    layered_nodes = itertools.product(range(n), range(d + 1))
    graph = nx.DiGraph()
    graph.add_nodes_from(layered_nodes)
    
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        
    graph.graph["num_layers"] = l
    graph.graph["width"] = n
    
    for i in range(n):
        for j in range(n):
            for k in range(d):
                graph.add_edge( (i,k), (j, k+1))
    
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        graph.nodes[x]["label"] = i
        i += 1
        graph.nodes[x]["weight"] = 0
    graph.graph["s"] = (0,0)
    graph.graph["t"] = (0,d)
    #viz(graph)          
    return graph

def create_split_chain_of_diamonds(pre_n = 4, l = 3):
    
    #An attempt at constructing a worst case example
    n = pre_n*3
    d = 2**l
    
    layered_nodes = itertools.product(range(n), range(d + 1))
    
    graph = nx.DiGraph()
    graph.add_nodes_from(layered_nodes)
    
    s = (0,0)
    t = (0,d)
    
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        
    graph.graph["num_layers"] = l
    graph.graph["width"] = n
    
    for i in range(n):
        if i % 3 == 1:
            graph.add_edge(s, (i, 1))
            graph.add_edge( ( i, d - 1), t)
    
    for l in range(d):
        if l % 2 == 1 and l != 0 and l != d- 1:
            for k in range(n):
                if k % 3 == 1:
                    #graph.add_edge( (l, k), (l+1, k-1))
                    graph.add_edge( (k, l), (k -1, l+1))

                    #graph.add_edge( (l,k), (l + 1, k + 1))
                    graph.add_edge( (k,l), ( k+1, l+1))
        if l % 2 == 0 and l != 0 and l != d:
            for k in range(n):
                if k % 3 == 1:
                    #graph.add_edge( (l, k-1), (l+1, k))
                    graph.add_edge( (k-1, l), (k, l+1))
                    #graph.add_edge( (l,k + 1), (l + 1, k))
                    graph.add_edge( (k+1, l), (k, l+1))
    
    for x in graph.nodes():
        #print(x)
        graph.nodes[x]["pos"] = np.array([x[0], x[1]])
        graph.nodes[x]["label"] = i
        i += 1
        graph.nodes[x]["weight"] = 0
    graph.graph["s"] = (0,0)
    graph.graph["t"] = (0,d)
    #viz(graph)          
    return graph


def check_unique_path(graph):
    ##Checks whether there is a unique min weight path from s to t. Algorithm tests the disambiguation requirement layer by layer. [TODO: Maybe another algorithm for testing min-unique st-path would lead to a different disambiguation requirement? Is it possible to use the randomness adaptively, by finding where the min-uniqueness breaks and then rerolling the hash function, e.g. by taking a step on the expander?]
    #E.g. compare here: https://networkx.github.io/documentation/stable/reference/algorithms/shortest_paths.html
    s = graph.graph["s"]
    t = graph.graph["t"]
    if nx.has_path(graph, s,t):
        paths = nx.all_shortest_paths(graph, s,t, weight = "weight")
        path0= next(paths)
        try:
            path1 = next(paths)
            return 2
            #meaning, at least 2
        except StopIteration:
            return 1
    else:
        return 0
    
def new_hash_function(r):
    # Produces a pairwise independent hash function h : [m]-> [r] 
    #We'll assume r > m, and that r is prime.
    
    #NB: Dropping the modulus keeps the collision probability down, although it's no longer uniform, and the range is different (r^2 instead of r). This is similar to shifting? What happens for random shifts? I.e. multiplication in N(atural numbers) against a random number randbelow(r). TODO.
    if not sympy.isprime(r):
        return False
    
    a = secrets.randbelow(r)
    b = secrets.randbelow(r)
    
    def hash_function(x):
        return (a*x + b) % r, r
    
    return hash_function

def step(hash_function, walk = "Expander"):
    b = hash_function(0)[0]
    a = hash_function(1)[0] - b
    r = hash_function(0)[1]
    if walk == "Frozen":
        neighbors = [(a,b)]
    if walk == "Fresh":
        neighbors = [(secrets.randbelow(r), secrets.randbelow(r))]    
    if walk == "Expander":
        neighbors = [(a,b), (a + 1, b), (a, b + 1), (a, a + b), ( -1 * b , a)]
    if walk == "Simple":
        neighbors = [(a,b), (a + 1, b), (a - 1, b)]
    if walk == "FirstCoordExpander":
        if a == 0:
            target = 0
        if a != 0:
            target = pow(a, r-2, r)
        neighbors = [(a,b), (a + 1, b), (a - 1, b), (target, b)]

        
        
    step = secrets.choice(neighbors)
    
    a = step[0]
    b = step[1]
    
    noshift = True
    #Shift is irrelevant for disambiguation condition.
    if noshift == True:
        b = 0
        
    def hash_function(x):
        return (a*x + b) % r, r
    
    return hash_function    
    
    
    


def pure_hashing_assign_weights(graph, walk = "Expander"):
    #Via Pure Hashing Approach
    
    r_value = nextprime(graph.graph["width"]**6)
    #r_value = nextprime((len(graph))**6) 
    
    l = graph.graph["num_layers"]
    n = graph.graph["width"]
    
    hash_function = new_hash_function(r_value)
    
    for k in range(l):
        hash_function = step(hash_function, walk)
        #The middle layers over all blocks of depth 2^{k+1}.  L = Union_{odd i \in [2^{l - k }]} V_{i 2^k}
        L = []
        for i in range(2**(l - k)):
            if i % 2 == 1:
                for j in range(n):
                    L.append( (j, i * (2**k)))
        for x in L:
            graph.nodes[x]["weight"] += hash_function(graph.nodes[x]["label"])[0]
                
    return graph


def search_for_bad_graphs():
    print("searching for bad graphs")
    f = open("random_search_data.txt", 'w')
    num_trials = 100
    n = 10
    l = 3
    r = 5
    index = 0
    bad_graphs = []
    graph_list = generate_unions_of_paths(n,l,r, random = True)
    #graph_list = [disjoint_paths(n, 6) for n in range(5,10)]
    for graph in graph_list:
            if index > 1000000:
                return "Done"
            index += 1
            if index % 1000 == 0:
                print(index)
            #viz(graph)
            if nx.has_path(graph, graph.graph["s"],graph.graph["t"]):
                f.write('\n')
                #for walk_label in ["Frozen", "Simple", "Expander","FirstCoordExpander","Fresh"]:
                for walk_label in ["Frozen", "Fresh"]:
    
                    uniques = 0
                    zeros = 0
                    for i in range(num_trials):
                        graph = pure_hashing_assign_weights(graph, walk = walk_label)
                        #viz(graph)
                        graph = node_weights_to_edge_weights(graph)
                        paths = check_unique_path(graph)
                        #print(paths)
                        if paths == 1:
                            uniques += 1
                        if paths == 0:
                            zeros += 1

                    report = str([walk_label, zeros/ num_trials, uniques / num_trials])
                    if uniques < 30:
                        print("found one")
                        viz(graph)
                        bad_graphs.append(graph)
                        print(report)
                        f.write(report)
                        f.write('\n')
                        THIS_FOLDER = 'C:\\Users\\lnajt\\Documents\\GitHub\\TinyProjects\\Pseudorandomness\\Graphs' 
                        my_file = os.path.join(THIS_FOLDER, str(hash(graph)))    
                        nx.write_gpickle(graph, str("badgraph_") + my_file)
                
    

def node_weights_to_edge_weights(graph):
    #Updates the edge weights based on node weights.
    #Profiler says this is the bottleneck. That makes no sense...
    for e in graph.edges():
        graph.edges[e]["weight"] = graph.nodes[e[0]]["weight"] + graph.nodes[e[1]]["weight"]
        
    return graph

#separate bad instances from bad hash functions
    


def test_custom_graph(graph, num_trials = 100):
    #tests how many hash functions cause graph to have a unique min path
    uniques = 0
    zeros = 0
    for i in range(num_trials):
        graph = pure_hashing_assign_weights(graph, walk = "Frozen")
        graph = node_weights_to_edge_weights(graph)
        paths = check_unique_path(graph)
        #print(paths)
        if paths == 1:
            uniques += 1
        if paths == 0:
            zeros += 1
    report = str([zeros/ num_trials, uniques / num_trials])
    print(report)
    return uniques / num_trials
    
def test_parallel_chains_of_diamonds():
    '''
    #
    Note that the width 1 case is not worst case for fresh; the only way that this fails is if $a = 0$.
    #The wider cases also do not seem to be worst case.
    '''
    
    f = open("worst_case_data.txt", 'w')
    num_trials = 100
    for width in [2,5,10,20]:
        f.write('\n')
        for l in range(3,5):
            graph = create_split_chain_of_diamonds(width, l)
            #graph= complete_layered_digraph(width, l) #NB: Obviously complete case 
            #is fine, because as long as weights are distinct the unique min takes one from each row
            viz(graph)
            f.write('\n')
            #for walk_label in ["Frozen", "Simple", "Expander","FirstCoordExpander","Fresh"]:
            for walk_label in ["Frozen", "Fresh"]:

                uniques = 0
                zeros = 0
                for i in range(num_trials):
                    graph = pure_hashing_assign_weights(graph, walk = walk_label)
                    #viz(graph)
                    graph = node_weights_to_edge_weights(graph)
                    paths = check_unique_path(graph)
                    #print(paths)
                    if paths == 1:
                        uniques += 1
                    if paths == 0:
                        zeros += 1
                report = str([width, l, walk_label, zeros/ num_trials, uniques / num_trials])
                print(report)
                f.write(report)
                f.write('\n')
    

#test_parallel_chains_of_diamonds()

def test_average_case():
    f = open("disambiguation_data3.txt", 'w')
    num_trials = 50
    num_graphs = 4
    bad_graphs = []
    for width in [80]:
        for density in [.3 , .2,.1,.05]:
            f.write('\n')
            for l in range(11,13):
                
    
                f.write('\n')
                #for walk_label in ["Frozen", "Simple", "Expander","FirstCoordExpander","Fresh"]:
                for walk_label in ["Frozen"]:
                    unique_ratios= []
                    for j in range(num_graphs):
                        graph = create_layered_digraph(width,l, density)
                        
                        while not nx.has_path(graph, graph.graph["s"],graph.graph["t"]):
                            graph = create_layered_digraph(width,l, density)
                        #print("doing trials")
                        graph.graph["density"] = density
                        uniques = 0
                        zeros = 0
                        for i in range(num_trials):
                            #It makes no sense that putting graph resample here changes the aggregate statistics! (?)
                            #graph = create_layered_digraph(width,l, density)
                            graph = pure_hashing_assign_weights(graph, walk = walk_label)
                            #viz(graph)
                            graph = node_weights_to_edge_weights(graph)
                            paths = check_unique_path(graph)
                            #print(paths)
                            if paths == 1:
                                uniques += 1
                            if paths == 0:
                                zeros += 1
                        unique_ratios.append(uniques / num_trials)
                        if walk_label == "Frozen" and uniques < 5:
                            bad_graphs.append(graph)
                    report = str([width, density, l, walk_label, zeros/ num_trials*num_graphs, np.min(unique_ratios)])
                    print(report)
                    f.write(report)
                    f.write('\n')
    #save(bad_graphs)
    #viz(graph)
   
#test_average_case()                 
def save(bad_graphs):
                    
    THIS_FOLDER = 'C:\\Users\\lnajt\\Documents\\GitHub\\TinyProjects\\Pseudorandomness\\Graphs'
    
    for graph in bad_graphs:
        my_file = os.path.join(THIS_FOLDER, str(hash(graph)))
    
        nx.write_gpickle(graph, my_file)
    
    bad_graphs = []
    for f in os.listdir('.'):
        if os.path.isfile(f):
          bad_graphs.append(nx.read_gpickle(f))
    #Something is wrong -- graph theory is showing no uniques at all, even for fresh, which is 
        #guaranteed to work...
    
    truly_bad_graphs = []
    for graph in bad_graphs:
        num_trials = 100
        for walk_label in ["Frozen", "Fresh", "None"]:
        #for walk_label in ["Fresh"]:
            uniques = 0
            zeros = 0
            for i in range(num_trials):
                graph = pure_hashing_assign_weights(graph, walk = walk_label)
                graph = node_weights_to_edge_weights(graph)
                paths = check_unique_path(graph)
                if paths == 1:
                    uniques += 1
                if paths == 0:
                    zeros += 1
            if walk_label == "Frozen" and uniques/num_trials <= .1:
                print("found bad one")
                truly_bad_graphs.append(graph)
            print(walk_label, uniques  , zeros)
            
            
            
    #SOMETHING IS WRONG: These truly bad graphs also give 0 for the fresh hashes. 
            #Okay, found the problem -- it seems like some up edges are added on the last layer?
    for graph in truly_bad_graphs:
        print(nx.has_path(graph, graph.graph["s"],graph.graph["t"]))
        num_trials = 100000
        for walk_label in ["Frozen", "Fresh"]:
        #for walk_label in ["Fresh"]:
            uniques = 0
            zeros = 0
            for i in range(num_trials):
                graph = pure_hashing_assign_weights(graph, walk = walk_label)
                graph = node_weights_to_edge_weights(graph)
                paths = check_unique_path(graph)
                if paths == 1:
                    uniques += 1
                if paths == 0:
                    zeros += 1
            print(walk_label, uniques  , zeros)
        

#search_for_bad_graphs()

    
def deletion_search(l = 2, n = 3, num_trials = 10):
    '''
    
    initial_graph is the initial graph
    
    If there exists a hash function of weight size r that causes F to be min-unique
    Then deletes one of the edges of graph that is part of the min-unique set
    Keeps running until either min-uniqueness is broken for all hash functions h
    or graph is disconnected.
    
    instead of trying every single hash function, will try num_trials random hashes
    
    '''
    initial_graph = complete_layered_digraph(l,n)
    graph = copy.deepcopy(initial_graph) 
    s = graph.graph["s"]
    t = graph.graph["t"]
    i = 0
    
    while nx.has_path(graph, s,t):
        i += 1

        uniques = 0
        for i in range(num_trials):
                graph = pure_hashing_assign_weights(graph, walk = "Frozen")
                graph = node_weights_to_edge_weights(graph)
                paths = check_unique_path(graph)
                if paths == 1:
                    uniques += 1
                    path = list(nx.all_shortest_paths(graph, s,t, weight = "weight"))[0]
                    path_edges = path_to_edge(path)
                    edge = random.choice(path_edges)
                    graph.remove_edge(edge[0], edge[1])
                    
        if nx.has_path(graph, graph.graph["s"], graph.graph["t"]):
            if uniques == 0:
                print("found graph", len(graph.edges()))
                viz(graph)
                return graph
        else:
            #print("disconnected, restarting")
            graph = copy.deepcopy(initial_graph)
            s = graph.graph["s"]
            t = graph.graph["t"]

for num_repairs in [20,25,30]:
    print(num_repairs)
    for i in range(10):
        candidate = deletion_search(4, 4, num_repairs)
        #This means that candidate was patched for num_repairs hash functions, and remained connected
        test_custom_graph(candidate) 
            
    
    
    
    
    
    
    
    
    
    
    
'''Observations:
   For Hash-Once = True, on (10,8), chance of min-unique drops to zero.The pictures this produces are pretty though. 
   For Hash-Once = False, on (10,8), chance of min-unique is around .8.
   For Expander, on (10,8), chance of min-unique is around .25. This steadily decreases as the number of layers increases. But doesn't increase super fast? Some of the figures it produces are interesting in their similarity to the hash once. 
   For Torus Random walk -- chance of min unique is similar. I think this is because the bad set is pretty explicit as a bunch of vertical lines? But then why doesn't the single chosen once for all hash work? 
   
10 0.5 8 Simple 0.0 0.25
10 0.5 8 Expander 0.0 0.28
    
   TODO: 
        a) Can you work out the expander hash case in the complete graph version?
        b) Can you find nextprime in log-space? Or do you need to use a different hash function?
        c) For the disambiguation requirement, you don't need the hashes to be uniform, just to have low CP. But isn't this achieved by taking f(x) = ax for a random (nonzero) a? 
        d) The bad set depends on the previously visited hashes (and the layered digraph) -- even if you have bounds on its size (like n^12/n^2), what's to prevent it from clustering up around the current hash function, in the currently chosen graph structure. It seems like some additional structure on the set of bad hashes is necessary. The bad hash functions are those that are the solutions to a set of equations, basically of the form $a = c(s,t,x,x') / (x - x'), where c is the difference of the weights of the relevant min paths. If c can be different from each (x,x'), I think this can be arbitrary, but presumably there is some correlation between them?
        e) Is it possible to use the randomness adaptively, by finding where the min-uniqueness breaks and then rerolling the hash function, e.g. by taking a step on the expander?
        f) Maybe instead want a hitting sampler on the set of hash functions? Some discussion here: http://www.wisdom.weizmann.ac.il/~oded/PDF/samplers.pdf but the parameters are not good enough.
    
    The set of bad hash functions is a union of lines. This is since the value of b in ax + b doesn't change the disambiguation requirements p + f(x) = q + f(x'). So only an expander on the first coordinate is necessary... ? 
'''