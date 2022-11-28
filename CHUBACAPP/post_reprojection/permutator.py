import numpy as np
import random as rd

def get_score(M, keep):
    score = 0
    for i in range(len(keep)):
        if keep[i]:
            for j in range(len(keep)):
                if keep[j]:
                    score+= M[i][j]
    return score - np.sum(keep)

def forward(M):
    keep = np.zeros(len(M))
    for i in range(len(keep)):
        new_keep = np.copy(keep)
        new_keep[i] = 1
        score = get_score(M, new_keep)
        if score == 0:
            keep = np.copy(new_keep)
    return keep

def permutate(M):
    keep = np.ones(len(M))
    min_score = 99999
    while min_score > 0:
        min_i = 0
        min_score = 99999
        new_keep = np.copy(keep)
        for i in range(len(keep)):
            new_keep[i] = 0
            score = get_score(M, new_keep)
            if score < min_score:
                min_i = i
                min_score = score
            new_keep[i] = 1
        print("Score: {} . Ends at 0".format(min_score))
        keep[min_i] = 0
    return(keep)
