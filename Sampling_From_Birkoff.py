# -*- coding: utf-8 -*-
'''
Some comments:
    
    - The algorithm starts very slowly from the identity matrix. 
    A better place to start it is from the doubly stochastic matrix which 
    has the same value for each entry.
    
    - For ball hopping ... I'm not sure what the right delta is. Following the paper, I set it around 1/ sqrt(n)
    - I also implemented hit and run...
    
How to use:
    
    To use this, run build_samples(dimension, steps)
    and input n for dimension if matrices are nxn
    and steps is number of steps to run
    
    defaults are starting_matrix = "center", sample_type = "uniform", method = "hitandrun"
    
Made in response to stack exchange question here: https://math.stackexchange.com/questions/12584/how-do-i-generate-doubly-stochastic-matrices-uniform-randomly
    '''


  
import numpy as np
from scipy.spatial import ConvexHull
import random
import scipy

###Linear algebra tools:

def project_to_birkoff(matrix):
    '''This projects a matrix to the linear space that the Birkoff polytope spans
    
    :vector: The input vector
    '''
    n = len(matrix)
    T = []
    E_ij = np.zeros([n, n])
    for i in range(n):
        for j in range(n):            
            E_ij[i,j] = 1
            out_ij = T_map(E_ij)
            T.append(out_ij)            
            E_ij[i,j] = 0
    T = np.asarray(T).T
    T_plus = np.linalg.pinv(T)
    I = np.identity(n**2)
    Q = I - np.matmul(T_plus, T)
    
    
    return flattened_multiplication(matrix, Q)

def flattened_multiplication(matrix, Q):
    '''This flattens matrix by making the vector v that is the row vectors in order
    Then it makes the vector vQ
    Then it unflattens vQ and returns that
    
    '''
    shape = matrix.shape
    v = matrix.flatten(order = 'C')
    new_v = np.matmul(v,Q)
    matrix = new_v.reshape(shape, order = 'C')
    return matrix
    
    
def T_map(matrix):
    n = len(matrix)
    ones = np.ones(n)
    first_coordinate = np.matmul(matrix, ones)
    second_coordinate = np.matmul(matrix.T, ones)
    output_vector = np.concatenate((first_coordinate, second_coordinate), 0)
    return output_vector


#dimension = 4
#list_of_matrices = []
#matrix = np.ones([dimension, dimension]) / dimension
#project_to_birkoff(matrix) + matrix
#Sanity check: The matrix with the same entry in each row projects to the zero 
#matrix... since both are the unique fixued points under permuting  rows and colums arbirarily...


def in_polytope(matrix):
    '''This takes a matrix in V^0, and checks that the entries are in [0,1]
    Note -- the linear part of the conditions to be a doubly stochastic matrix are 
    already assumed to hold'''
    
    n = matrix.shape[0]
    for i in range(n):
        for j in range(n):
            value = matrix[i][j]
            if value > 1:
                return False
            if value < 0:
                return False
    
    return True

###Hit and run:
    

def hit_and_run_step(matrix, a_priori_lower, a_priori_upper):
    direction = project_to_birkoff(np.random.normal(0,1,matrix.shape))
    direction = direction / np.linalg.norm(direction)
    lower = a_priori_lower
    upper = a_priori_upper
    while True:
        a = np.random.uniform(lower, upper)
        new_matrix = matrix + a * direction
        if in_polytope(new_matrix):
            return new_matrix
        else:
            if a > 0:
                upper = a
            if a < 0:
                lower = a

def hit_and_run_chain(matrix, steps, a_priori_lower, a_priori_upper):
    samples = []
    samples.append(matrix)
    for i in range(steps):
        new_matrix = hit_and_run_step(matrix, a_priori_lower, a_priori_upper)
        matrix = new_matrix
        samples.append(new_matrix)
    return samples

###Ball hopping tools:

def ball_hop_propose_step(matrix, delta):
    '''This takes a Birkoff matrix, and proposes a delta step...
    
    We are going to ignore the problems with round off by never checking the 
    linear conditions, and hoping that they come out in the wash...
    '''
    direction = project_to_birkoff(np.random.normal(0,1,matrix.shape))
    direction = direction / np.linalg.norm(direction)
    n = matrix.shape[0]
    ambient_dimension = n**2 - 2*n + 1
    alpha = np.power(np.random.uniform(), 1/ambient_dimension)
    '''
    If U is a uniform([0,1]), and alpha = U^{1/d}
    then P( alpha <= x) = P(U^{1/d} <= x) = P(U <= x^d) = x^d
    So the probability that the sampled vector lies in a sphere of 
    radius x is proportional to x^d, which is correct, since the volume
    of a ball of radius x is C*x^d. 
    
    
    '''
    
    step_vector = alpha* delta* direction
    
    return matrix + step_vector

def ball_hop_markov_chain(matrix, delta, steps):
    samples = []
    samples.append(matrix)
    for i in range(steps):
        new_matrix = ball_hop_propose_step(matrix, delta)
        if in_polytope(new_matrix):
            matrix = new_matrix
            samples.append(matrix)
        else:
            samples.append(matrix)
    return samples

def ball_hop_only_new_samples(matrix, delta, steps):
    samples = []
    samples.append(matrix)
    i= 0
    while i < steps:
        new_matrix = ball_hop_propose_step(matrix, delta)
        if in_polytope(new_matrix):
            matrix = new_matrix
            samples.append(matrix)
            i += 1
    return samples

######
    
def build_samples(dimension, steps, starting_matrix = "center", sample_type = "uniform", method = "hitandrun"):
    '''This runs the build samples method using the constants in the Lovasz paper
    
    :dimension: the dimension of the matrices, i.e. they will be dimension by dimension
    :steps: number of steps to take
    
    
    '''  
    if starting_matrix == "center":
        matrix = np.ones([dimension, dimension]) / dimension
    if starting_matrix == "identity":
        matrix = np.identity(dimension)
        
    if method == "ballhop":
        delta = .5 / np.sqrt(dimension)
        if sample_type == "uniform":
            return ball_hop_markov_chain(matrix, delta, steps)
        if sample_type == "only new":
            return ball_hop_only_new_samples(matrix, delta, steps)
        
    if method == "hitandrun":
        '''since the Birkoff polytope is contained in [0,1]^n
        and upper bound on the diameter is sqrt(n)
        
        '''
        samples = hit_and_run_chain(matrix, steps, -1 * np.sqrt(dimension), np.sqrt(dimension))
        return samples

##Validating code:

def check_doubly_stochastic(matrix):
    '''Returns false if the matrix is not (close to) doubly stochastic
    '''
    n = matrix.shape[0]
    ones = np.ones(n)
    rows = np.matmul(matrix, ones)
    columns = np.matmul(matrix.T, ones)
    if not in_polytope(matrix):
        return (False, "was not in polytope", 0)
    if not np.allclose(rows, ones):
        return (False, rows, columns)
    if not np.allclose(columns, ones):
        return (False, rows, columns)
    return (True, rows, columns)

def testing_code():
    '''This is just to make sure the code is doing what it is supposed to be doing
    '''
    samples = build_samples(4, 1000)
    for i in range(len(samples)):
        truth, rows, columns = check_doubly_stochastic(samples[i])
        if not truth:
            print(i, rows, columns)
            
def get_statistics():
    dimension = 3
    steps = 10000
    samples = build_samples(dimension, steps)
    sample_matrix =np.asarray(  [matrix.flatten() for matrix in samples])
    print([ np.mean([ v[k ] for v in sample_matrix ]) for k in range(dimension**2)])
    samples = build_samples(dimension, steps, method = "ballhop")
    sample_matrix =np.asarray(  [matrix.flatten() for matrix in samples])
    print([ np.mean([ v[k ] for v in sample_matrix ]) for k in range(dimension**2)])
    
    samples = build_samples(dimension, steps, starting_matrix="identity")
    sample_matrix =np.asarray(  [matrix.flatten() for matrix in samples])
    print([ np.mean([ v[k ] for v in sample_matrix ]) for k in range(dimension**2)])
    samples = build_samples(dimension, steps, starting_matrix="identity",method = "ballhop")
    sample_matrix =np.asarray(  [matrix.flatten() for matrix in samples])
    print([ np.mean([ v[k ] for v in sample_matrix ]) for k in range(dimension**2)])
    
def compare_volume(dimension, steps):
    '''Compares the estimated volume to the true volume in small dimensions'''
    dimension = 2
    steps = 200000
    samples = build_samples(dimension, steps, starting_matrix="center")
    
    center_matrix = (np.ones([dimension, dimension]) / dimension).flatten()
    sample_matrix =np.asarray(  [list(matrix.flatten()) - center_matrix for matrix in samples])
    while np.linalg.matrix_rank(sample_matrix) != dimension**2 - 2 * dimension + 1:
        #Make sure we get the right dimension...        
        samples = build_samples(dimension, steps, starting_matrix="center")
        center_matrix = (np.ones([dimension, dimension]) / dimension).flatten()
        sample_matrix =np.asarray(  [list(matrix.flatten()) - center_matrix for matrix in samples])
    print(    np.linalg.matrix_rank(sample_matrix))
    #We subtract center_matrix to make this linear algebra...
    basis = scipy.linalg.orth(sample_matrix.T).T
    coordinates = np.linalg.lstsq(sample_matrix.T, basis.T)[0]
    maxim = max(coordinates)
    minim = min(coordinates)
    if dimension == 2:
        print(maxim - minim)
    if dimension >= 3:
        MLE_polytope = ConvexHull(coordinates)
        print(MLE_polytope.volume)
            
        
        
        '''On hit and run:
            
            https://pdfs.semanticscholar.org/1fdd/84ffb88fe03512f39ccc16b591fc521e40c8.pdf
        
        
        '''
'''
Let $V \subset M_n(\mathbb{R})$ be the affinespace of matrices $M$ so that $M 1 = 1$ and $1^T M = 1$, where $1$ is the all ones matrix. (I.e. that the row and column sums are all one.)

Let $V^0$ be the vector space so that $V^0 + I = V$. I.e., $V^0$ is the kernel of $M \to (M1, 1^T M)$.

Now $B = V \cap \{ M \geq 0\}$, where $M \geq 0$ means that all of the entries of $M$ are greater than zero.

$B$ is a polytope of full dimension inside of $V$. Therefore, we can sample a random bistochastic matrix using the following algorithm:

0) Initialize a list $L$.

1) Start with a seed matrix $M \in B$.

2) Pick a random vector $v$ in the the $\delta$-ball of $V^0$. 

3) Consider the matrix $M + v$.

4) If $M + v \in B$: add $M + v$ to $L$, and set $M = M + v$.
Else: Go back to 2.



Here is a simple proof that the stationary distribution of this algorithm is uniform over the partition. (Hopefully this will also clarify what the algorithm is doing)


The algorithm as it is may not be that efficient. For example, if delta is 
too large, and we are in a corner of our polytope, we may spend a lot of time 
rejecting steps. On the other hand, if delta is to small, we will have a hard
time moving around the polytope.

In this paper, http://web.cs.elte.hu/~lovasz/vol5.pdf , Lovasz et. al. describe
an algorithm that speeds up this process considerably.

...



---------------

To do step 2, it suffices to find an orthogonal projector from $M_n(\mathbb{R})$ onto $V^0$. Let $T$ be the map $T(M) = (M1, 1^TM)$. Then $V^0$ is the kernel of $T$. If $T^{+}$ is the pseudoinverse of $T$, then $I - T^{+}T$ is an orthogonal projector onto $V^0$. (See: https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse#Projectors )

Thus, if $Y$ is a chosen from a standard Gausssian in $M_n(\mathbb{R})$, $(I - T^{+}T)Y$, is a standard Gaussian in $V^0$. Hence $\hat{a} = \frac{ (I - T^{+}T)Y } {|| (I - T^{+}T)Y || }$ is a random direction in $V^0$, and we can pick a number $\alpha$ from $[0,\delta]$ s that $\alpha \hat{a}$ is a random vector in the unit ball of $V^0$.

Working out the distribution with which to draw $\alpha$ depends on computing that the dimension of $V^0$ is $n^2 - 2n + 1$. (See https://en.wikipedia.org/wiki/N-sphere#Volume_and_surface_area for the formulas...)

Computing this dimension is a nice exercise, but for completeness I'll sketch the argument: 

First, you should show that the rank of $T$ is at most $2n - 1$. To do this, observe that the equations describing doubly stochastic matrices have one redundancy -- namely, if I add up the equations that say that the columns sum to zero, and subtract away the equations that say that the rows sum to zero, except for the last row, the equation that says the last row sums to zero follows.

Next, you can show that the rank of $T$ is at least $2n - 1$. To do this, observe that $T ( e_{ij}) = (e_j, e_i)$.  So, within the image we have the set of $2n - 1$ vectors that are $\{ (e_i, e_1), (e_1, e_j) : i = 1, \ldots, n, j = 1, \ldots n \}$. We can check that these are linearly independent: If $a (e_1, e_1) + \Sigma_{i > 1} a_i (e_i, e_1) + \Sigma_{j > 1} b_j (e_1, e_j) = 0$, then we get the following equations:

$a_i e_i = 0$ for $i > 1$, $b_j e_j = 0$ for $j > 1$, and $a (e_1 , e_1) = 0$, which implies that $a = 0 = a_i = 0 = \ldots = b_j = 0$.

---

On the selection of parameters for the algorithm: 
    We lok at algorihtm 4.11

---

Here is some python code that implements this:  https://github.com/LorenzoNajt/TinyProjects/blob/master/Sampling_From_Birkoff.py

---

We can sanity check this code by using it to estimate the volume of the Birkoff polytope, which is known in small dimension:
    
To do this, we will use algorithm 6.1 from the Lovasz paper.
    
'''