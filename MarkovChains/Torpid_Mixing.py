#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 27 15:20:30 2018

@author: Lorenzo Najt
"""
import random
import networkx as nx
import math
import copy
import os
from itertools import chain, combinations
import matplotlib.pyplot as plt
import numpy as np
import pickle
from pathlib import Path as FilePath
from Facefinder import depth_k_refine
    
import matplotlib.animation


#Got this code from stack exchange:
def powerset(iterable):
    """
    powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    """
    xs = list(iterable)
    # note we return an iterator rather than a list
    return chain.from_iterable(combinations(xs,n) for n in range(len(xs)+1))

alphabet = [0,1]

#levels = 2
#strings = [str(x) for x in alphabet]
#strings.append ( '')
#current_level = [str(x) for x in alphabet]
#for level in range(2):
#    next_level = [ t + str(x) for x in alphabet for t in current_level]
#    strings = strings + next_level
#    current_level = next_level
#
#G = nx.prefix_tree(strings)[0]

def add_level_data(m,tree):
    roots = []
    for n in tree.nodes():
        if tree.degree(n) == m:
            roots.append(n)
            tree.graph["root"] = roots[0]
    wet_set = set([roots[0]])
    dry_set = set()
    level = 0
    while wet_set != set():
        new_wets = set()
        for node in wet_set:
            dry_set.add(node)
            tree.nodes[node]["level"] = level
            neighbors = tree.neighbors(node)
            for n in neighbors:
                if n not in dry_set:
                    new_wets.add(n)
        level += 1
        wet_set = new_wets
    return tree


def construct_doubled_tree(m = 2,k  = 3):
    G = nx.balanced_tree(m,k)
    H = nx.balanced_tree(m,k)
    G = add_level_data(m,G)
    H = add_level_data(m,H)
    G_leaves = []
    for x in G.nodes:
        if G.degree(x) == 1:
           G_leaves.append(x)
    H_leaves = []
    for x in H.nodes:
        if H.degree(x) == 1:
            H_leaves.append(x)
        H.node[x]["half"] = "H"
    
    G_not_leaves = []
    for y in G.nodes():
        if y not in G_leaves:
            G_not_leaves.append(y)
    
    nodes_to_add = [str(y) + "G" for y in G_not_leaves]
    H.add_nodes_from(nodes_to_add)
    for n in G_not_leaves:
        H.node[str(n) + "G"]["level"] = G.node[n]["level"]
        H.node[str(n) + "G"]["half"] = "G"
    
    for y in G_not_leaves:
        for x in G.neighbors(y):
            if x in G_leaves:
                H.add_edge( x, str(y) + "G")
            else:
                H.add_edge(str(x) + "G", str(y) + "G")
    H.graph["depth"] = k
    H.name = "doubled_tree"
    roots = [H.graph["root"], str(G.graph["root"]) + "G"]
    H.graph["roots"] = roots
    return H


def get_neighbors(nodes, subset):
    #returns the n neighbors in the hypercube.
    neighbors = []
    for x in nodes:
        if x in subset:
            new_set = copy.deepcopy(subset)
            new_set.remove(x)
            neighbors.append(frozenset(new_set))
        if x not in subset:
            new_set = copy.deepcopy(subset)
            new_set.add(x)
            neighbors.append(frozenset(new_set))
    return neighbors

def min_choice(keys, function):
    #returns the key that minimizes the function
    running_min =  np.inf
    current_best = keys[0]
    for key in keys:
        if function[key] < running_min:
            running_min = function[key]
            current_best = key
    return current_best
            
def random_walk(graph, length, bal):
    path = []
    current = frozenset(graph.nodes())
    graph_size = len(current)
    nodes = set(graph.nodes())
    if bal == True:
        balanced_achieved = False
        while not balanced_achieved:
            neighbors = get_neighbors(nodes, set(current))
            legal_neighbors = []
            bal_score = {}
            for n in neighbors:
                if len(n) != 0 and len(n) != graph_size:
                    y = nodes - n
                    A = nx.subgraph(graph, n)
                    B = nx.subgraph(graph, y)
                    if nx.is_connected(A) and nx.is_connected(B):
                        legal_neighbors.append(n)
                        bal_score[n] = abs( len(y) - len(n))
            current = min_choice(legal_neighbors, bal_score)
            print(bal_score[current])
            if bal_score[current] < 4:
                balanced_achieved = True
    path.append(current)
    for i in range(length):
        neighbors = get_neighbors(nodes, set(current))
        legal_neighbors = []
        for n in neighbors:
            if len(n) != 0 and len(n) != graph_size:
                
                y = nodes - n
                if abs(len(y) - len(n)) < 4 or not bal:
                    A = nx.subgraph(graph, n)
                    B = nx.subgraph(graph, y)
                    if nx.is_connected(A) and nx.is_connected(B):
                        legal_neighbors.append(n)
            else:
                if not bal:
                    legal_neighbors.append(n)
        
        current = random.choice(legal_neighbors)
        path.append(current)
        if i % 1000 == 0:
            print(i)
    return path
                

def down_neighbors(nodes, subset):
    #returns the n neighbors that come by removing an element
    neighbors = []
    for x in nodes:
        if x in subset:
            new_set = copy.deepcopy(subset)
            new_set.remove(x)
            neighbors.append(frozenset(new_set))
    return neighbors
            
def assign_heights(T,k,m):
    #this is to make T easier to visualize
    roots = T.graph["roots"]
    for x in T.nodes:
        T.node[x]["touched"] = False
    root = roots[0]
    T.node[root]["Y"] = k
    T.node[root]["X"] = 0
    T.node[root]["touched"] = True
    level = k
    wet_set = set()
    wet_set.add(root)
    while level > 0:
        level += -1
        new_wets = set()
        for point in wet_set:
            sign = -1
            neighbors = list(T.neighbors(point))
            for n in neighbors:
                if T.node[n]["touched"] == False:
                    T.node[n]["touched"] = True
                    if level >= 0:
                        T.node[n]["X"] = T.node[point]["X"] + sign * (1/m)**(  k - T.node[point]["Y"] )
                        sign = sign + 2/(m-1)
                        T.node[n]["Y"] = level
                        new_wets.add(n)
        wet_set = new_wets                    
            
    root = roots[1]
    T.node[root]["Y"] = -1* k
    T.node[root]["X"] = 0
    T.node[root]["touched"] = True
    wet_set = set()
    wet_set.add(root)
    level = k
    while level > 0:
        level += -1
        new_wets = set()
        for point in wet_set:
            sign = -1
            neighbors = T.neighbors(point)
            for n in neighbors:
                if T.node[n]["touched"] == False:
                    T.node[n]["touched"] = True
                    if T.node[point]["Y"] < 0:
                        T.node[n]["X"] = T.node[point]["X"] + sign * (1/m)**( k + T.node[point]["Y"] )
                        sign = sign + 2/(m-1)
                        T.node[n]["Y"] = T.node[point]["Y"] + 1
                        new_wets.add(n)
        wet_set = new_wets
    return T
                        
  

def make_histogram(list_of_samples):
    values = {}
    for sample in list_of_samples:
        values[sample] = 0
    for sample in list_of_samples:
        values[sample] += 1
    return values

def reload_path(name):
    with open(name, "rb") as fp:   # Unpickling
        path = pickle.load(fp)
    return path

def make_path(size, steps, graph = 0, bal = False):
    #First check to see if there is a file 
    if graph == 0:
        T = construct_doubled_tree(size)
    else:
        T = graph
    name = str(T.name) + "steps" + str(steps)
    print(name)
    mydir = os.curdir
    filename = os.path.join(mydir, name)
    myfile = FilePath(filename)

    if myfile.is_file():
        print("found in directory")
        return reload_path(name), T

    #T = assign_heights(T,2)
    path = random_walk(T, steps, bal)

    with open(name, "wb") as fp:
        pickle.dump(path, fp)
    return path, T

def depth_weighted(n):
    running_sum = 0
    for x in n:
        running_sum += T.node[x]["level"]
    return running_sum

def middle(n):
    running_sum = 0
    for x in n:
        if T.node[x]["level"] == k:
            running_sum += 1
    return running_sum

def balance(n):
    #ignores middle, returns balance ratio between top and bottom halves
    #The intuition for this is to find a bottleneck similar to that describes for independent sets in Jerrum chapter 7...
    running_sum = 0
    for x in n:
        if T.node[x]["level"] != T.graph["depth"]:
            if T.node[x]["half"] == "H":
                running_sum += 1
            if T.node[x]["half"] == "G":
                running_sum += -1
    return running_sum

def weighted_balance(n):
    running_sum = 0
    for x in n:
        weight = 10**(k - T.node[x]["level"])
        if T.node[x]["level"] != T.graph["depth"]:
            if T.node[x]["half"] == "H":
                running_sum += weight
            if T.node[x]["half"] == "G":
                running_sum += -1 * weight
    return running_sum

def top_bottom(n):
    running_sum = 0
    for x in n:
        if T.node[x]["level"] == 0:
            if T.node[x]["half"] == "H":
                running_sum += 1
            if T.node[x]["half"] == "G":
                running_sum += -10
    return running_sum
def make_time_series(path, function = len):

    lengths = [function(x) for x in path]
    x_values = list(range(len(path)))
    plt.scatter(x_values, lengths)
    plt.show()

def make_hist(path, function = len):
    hist = make_histogram([function(x) for x in path])

    plt.bar(list(hist.keys()), hist.values(), color='g')
    plt.show()
    
    
def viz(T,k,n,m):
    T = assign_heights(T,k,m)
    for x in T.nodes():
        T.node[x]["pos"] = [T.node[x]["X"], T.node[x]["Y"]]
    for x in T.nodes():
        if x in n:
            T.node[x]["col"] = 1
        else:
            T.node[x]["col"] = 0
    values = [T.node[x]["col"] for x in T.nodes()]
    nx.draw(T, pos=nx.get_node_attributes(T, 'pos'), node_size = 200/k, width = .5, cmap=plt.get_cmap('jet'), node_color=values)
    

#def update(num):
#    ax.clear()
#
#    for x in T.nodes():
#        T.node[x]["pos"] = [T.node[x]["X"], T.node[x]["Y"]]
#    for x in T.nodes():
#        if x in path[num]:
#            T.node[x]["col"] = 1
#        else:
#            T.node[x]["col"] = 0
#    values = [T.node[x]["col"] for x in T.nodes()]
#    nx.draw(T, pos=nx.get_node_attributes(T, 'pos'), node_size = 200/k, width = .5, cmap=plt.get_cmap('jet'), node_color=values)
#
#
#    ax.set_xticks([])
#    ax.set_yticks([])
#  
  
def animate(T,k,path, size, num_frames = 2000, delay = 10):

    fig, ax = plt.subplots(figsize=(6,4))
    def update(num):
        ax.clear()
    
        for x in T.nodes():
            T.node[x]["pos"] = [T.node[x]["X"], T.node[x]["Y"]]
        for x in T.nodes():
            if x in path[num]:
                T.node[x]["col"] = 1
            else:
                T.node[x]["col"] = 0
        values = [T.node[x]["col"] for x in T.nodes()]
        nx.draw(T, pos=nx.get_node_attributes(T, 'pos'), node_size = 200/k, width = .5, cmap=plt.get_cmap('jet'), node_color=values)
    
    
        ax.set_xticks([])
        ax.set_yticks([])
    
    
    ani = matplotlib.animation.FuncAnimation(fig, update, frames=num_frames, interval=delay, repeat=True)
    plt.show()  
    name = str(T.name) + "path_for_size" + str(T.graph["size"]) + "steps" + str(T.graph["steps"]) + '.mp4'
    #ani.save(name, writer="ffmpeg")
    
#if you can compute the correct distribution and display it, that will measure failure to mix. Deviation from symmetry also does this.

def make_grid(k):
    
    G = nx.grid_graph([k,k])
    for x in G:
        G.node[x]["level"] = x[1]
        if x[1] == k:
            G.node[x]["half"] = "M"
        if x[1] > k:
            G.node[x]["half"] = "H"
        if x[1] < k:
            G.node[x]["half"] = "G"
        G.name = "gridgraph_size:" + str(k) +"_"
        G.graph["depth"]= k
        G.node[x]["X"] = x[0]
        G.node[x]["Y"] = x[1]
    return G

def replace_edges(G,k,m):
    #takes a graph G and replaces the edges with depth k doubled trees.
    #This is to investigate the observation that because these doubled trees have an attractor at the maximally unbalanced partition, it is unlikely that that they produce a link through which connectivity can flow.
    
    T = construct_doubled_tree(m,k)
    T = assign_heights(T,k,m)

    #can also add the spokes construction
    H = copy.deepcopy(G)

    edge_list = list(H.edges())
    for e in edge_list:
        H.remove_edge(e[0], e[1])
        H = glue(H,T, e[0], e[1])
    return H
    
    
    
def glue(G,S,a,b):
    #G and S have vertices named a and b, we glue them together along these vertices. The nodes in the copy of S have a label that identifies the edge they came from.
    #We also compute X and Y coordinates for visualization
    y_values = [S.node[x]["Y"] for x in S.nodes()]
    x_values = [S.node[x]["X"] for x in S.nodes()]
    gadget_height = abs( max(y_values) - min(y_values) )
    gadget_width = abs( max(x_values) - min(x_values))
    top = [0, max(y_values)]
    
    #print([ G.node[b]["X"], G.node[b]["Y"]])
    mapping = {0 : a, '0G' : b}
    S = nx.relabel_nodes(S, mapping)

    vertex_set = set()
    edge_label = "(" + str(a) + ","+ str(b) + ")" + ":"
    label_mapping = {}
    for x in S.nodes():
        if x in [a,b]:
            label_mapping[x] = x
        else:
            label_mapping[x] = edge_label + str(x)
    inv_label_map = {v: k for k, v in label_mapping.items()}
    location_dictionary = {}
    for x in G.nodes():
        vertex_set.add(x)
        location_dictionary[x] = [ G.node[x]["X"], G.node[x]["Y"]]
    #print("before mess, loc dictionary", location_dictionary)
    for x in S.nodes():
        vertex_set.add( label_mapping[x])
        
        
        
        
        a_coord = np.array([ G.node[a]["X"], G.node[a]["Y"]])
        b_coord = np.array([ G.node[b]["X"], G.node[b]["Y"]])
        
        
        
        
        relative = np.array([S.node[x]["X"]/gadget_width, S.node[x]["Y"]]) - np.array(top)
        
        
        
        edge_base = a_coord
        edge_vector = b_coord - a_coord
        edge_length = np.linalg.norm(edge_vector)
        normalized_edge_vector = edge_vector / edge_length
        
        
        
        height_scaling = edge_length / gadget_height 
        #print(height_scaling)
        
        
        rotation = np.array([ [-1* normalized_edge_vector[1], normalized_edge_vector[0]], [ normalized_edge_vector[0],  normalized_edge_vector[1]]]) * -1
        

        rotated_vector = np.matmul(rotation, relative)

        absolute = (rotated_vector) * height_scaling + edge_base
        absolute = list(absolute)
        location_dictionary[x] = [ absolute[0], absolute[1]]
        #sanity check -- top and bottom should end up with location the same as the original a and b ... this might be what is going wrong, and the error is propagating.
        
        
        
        
        
    #print(location_dictionary)
    H = nx.Graph()
    H.add_nodes_from(vertex_set)
    for e in G.edges():
        H.add_edge(e[0], e[1])
    for e in S.edges():
        H.add_edge(label_mapping[e[0]], label_mapping[e[1]])
#    print(location_dictionary)
#    print(label_mapping)
#    print(H.nodes())
    #print("NODES: ", H.nodes())
    for x in H.nodes():
        if x in inv_label_map.keys():
            location = location_dictionary[inv_label_map[x]]
        else:
            location = location_dictionary[x]
        H.node[x]["X"] = location[0]
        H.node[x]["Y"] = location[1]

    inverse_mapping = {a : 0, b : '0G'}
    S= nx.relabel_nodes(S, inverse_mapping)
    return H
        
    

global T


def draw_with_location(graph):
#    for x in graph.nodes():
#        graph.node[x]["pos"] = [graph.node[x]["X"], graph.node[x]["Y"]]

    nx.draw(graph, pos=nx.get_node_attributes(graph, 'pos'), node_size = 200/k, width = .5, cmap=plt.get_cmap('jet'))


def face_gadget():
    m = 3
    depth = 2
    graph = nx.grid_graph([m,m])
    graph.name = "grid_size_" + str(m)
    for x in graph.nodes():
        
        graph.node[x]["pos"] = np.array([x[0], x[1]])
    
    graph = depth_k_refine(graph,depth)
    
    draw_with_location(graph)
    
    num_frames = 401
    delay = 30
    bal = False

    path, T = make_path(10,num_frames, graph, bal)
    
    #stat = balance
    #stat_list = [stat(x) for x in path]
    #make_time_series(path, stat)
    
    #viz(T,gadget_depth, path[1000],gadget_width)
    #
    
    
    
    fig, ax = plt.subplots(figsize=(6,4))
    
    def update(num):
        ax.clear()
    
    
        for x in T.nodes():
            if x in path[num]:
                T.node[x]["col"] = 1
            else:
                T.node[x]["col"] = 0
        values = [T.node[x]["col"] for x in T.nodes()]
        nx.draw(T, pos=nx.get_node_attributes(T, 'pos'), node_size = 50/gadget_depth*gadget_width, width = .5, cmap=plt.get_cmap('jet'), node_color=values)
    
    
        ax.set_xticks([])
        ax.set_yticks([])
    
    
    ani = matplotlib.animation.FuncAnimation(fig, update, frames=num_frames, interval=delay, repeat=True)
    plt.show()  
    

def set_pos(graph):
    for x in graph.nodes():
        graph.node[x]["pos"] = [graph.node[x]["X"], graph.node[x]["Y"]]
    return graph 

def edge_gadget():
    k = 1
    grid_size = 4
    global gadget_depth
    global gadget_width
    gadget_depth = 1
    gadget_width = 5
    bal = False
    G = make_grid(grid_size)
    H = replace_edges(G,gadget_depth, gadget_width)
    H.name = str(G.name) + "_gadgetdepth:" + str(gadget_depth) + "_gadgetwidth:" + str(gadget_width) + "bal:" + str(bal)
    
    H = set_pos(H)
        
    draw_with_location(H)
    
    
    
    num_frames = 400
    delay = 30

    path, T = make_path(k,num_frames, H, bal)
    
    #stat = balance
    #stat_list = [stat(x) for x in path]
    #make_time_series(path, stat)
    
    #viz(T,gadget_depth, path[1000],gadget_width)
    #
    
    
    
    fig, ax = plt.subplots(figsize=(6,4))
    
    def update(num):
        ax.clear()
    
    
        for x in T.nodes():
            if x in path[num]:
                T.node[x]["col"] = 1
            else:
                T.node[x]["col"] = 0
        values = [T.node[x]["col"] for x in T.nodes()]
        nx.draw(T, pos=nx.get_node_attributes(T, 'pos'), node_size = 50/gadget_depth*gadget_width, width = .5, cmap=plt.get_cmap('jet'), node_color=values)
    
    
        ax.set_xticks([])
        ax.set_yticks([])
    
    
    ani = matplotlib.animation.FuncAnimation(fig, update, frames=num_frames, interval=delay, repeat=True)
    plt.show()  
    
    #name = str(H.name) +  "_steps:" + str(num_frames) + '.mp4'
    #ani.save(name, writer="ffmpeg")
    
    #animate(T,k,path,1000,10)

