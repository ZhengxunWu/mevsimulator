import networkx as nx
import random
import itertools
import numpy as np
from typing import Dict, List, Tuple

# number of nodes n
# number of byzantine / malicious nodes f
# gamma : order fairness parameter
# g : granularity

gamma = 4


class Tx:
    def __init__(self, content, timestamp, bucket=None):
        self.content = content
        self.timestamp = timestamp  # Unix timestamp
        self.bucket = bucket

    def __str__(self):
        return f"Transaction: {self.content} , {self.timestamp}"

    def __repr__(self):
        return f"Tx(content ='{self.content}', timestamp = {self.timestamp}, bucket = {self.bucket})"


# Node 1: [a,b,c,e,d]
# Node 2: [a,c,b,d,e]
# Node 3: [b,a,c,e,d]
# Node 4: [a,b,d,c,e]
# Node 5: [a,c,b,d,e]

# assume this is already sorted, i.e. an ordering
n_tx_lists = {1: [Tx("a",1326244364), Tx("b",1326244365), Tx("c",1326244366), Tx("e",1326244367), Tx("d",1326244368), Tx("f",1326244369), Tx("g",1326244370)],
              2: [Tx("a",1326244364), Tx("c",1326244365), Tx("b",1326244366), Tx("d",1326244367), Tx("e",1326244368), Tx("f",1326244369), Tx("g",1326244375)],
              3: [Tx("b",1326244364), Tx("a",1326244365), Tx("c",1326244366), Tx("e",1326244367), Tx("d",1326244368), Tx("f",1326244376)],
              4: [Tx("a",1326244364), Tx("b",1326244365), Tx("d",1326244366), Tx("c",1326244367), Tx("e",1326244368)],
              5: [Tx("a",1326244364), Tx("c",1326244365), Tx("b",1326244366), Tx("d",1326244367), Tx("e",1326244368)]
              }

starting_timestamp = 1326244364
granularity = 5
n_granularized_tx_lists = {}


def granularize(tx_ordering, starting_timestamp: int, granularity: int) -> List[Tx]:
    """Puts txs into buckets
    line 10-12
    All transactions with timestamps [0,g-1] are in the same bucket, [g, 2g-1] are in the same bucket etc.
    """
    for tx in tx_ordering:
        quotient = int((tx.timestamp - starting_timestamp) // granularity)
        tx.bucket = quotient
    return tx_ordering


def get_all_tx_in_batch(tx_list: Dict[int, Tx]) -> Dict[int, Tx]:
    # TODO
    return


def compute_initial_set_of_edges(tx_dict: Dict) -> Tuple[nx.DiGraph, Dict]:
    """
    line 15-25

    Args:

    Returns:
      need not be complete. Graph need not be acyclic
    """
    nodes = set()
    for key in tx_dict:
        for tx in tx_dict[key]:
            if tx.content not in nodes:
                nodes.add(tx.content)
    nodes = sorted(nodes)
    print("nodes:", nodes)
    n = len(nodes)

    # TODO: Some data processing and cleaning to get the following simplified_list
    simplified_list = [
        ["a", "b", "c", "e", "d"],
        ["a", "c", "b", "d", "e"],
        ["b", "a", "c", "e", "d"],
        ["a", "b", "d", "c", "e"],
        ["a", "c", "b", "d", "e"],
    ]

    edge_candidates = list(itertools.combinations(nodes, 2))
    edge_candidates = sorted(edge_candidates, key=lambda x: (x[0], x[1]))
    assert len(edge_candidates) == ((n ** 2 - n) / 2)  # O(n^2) combinations
    print("edge_candidates: ", edge_candidates)

    # Get the indices of each tx in every nodes's vote
    indices = {}
    for i in nodes:
        idx = []
        for row in simplified_list:
            idx.append(row.index(i))
        indices[i] = np.array(idx)
    print("indices:", indices)
    # 'a': [0,0,1,0,0],
    # 'b': [1,2,0,1,2],
    # 'c': [2,1,2,3,1],
    # 'd': [4,3,4,2,3],
    # 'e': [3,4,3,4,4]

    # Compute the differences between all pairs of txs, a negative value in this matrix means key[0] is in front of key[1]
    pairs_dict = {}
    for key in edge_candidates:
        pairs_dict[key] = indices[key[0]] - indices[key[1]]
    print("pairs_dict:", pairs_dict)
    # ('a', 'b'): array([-1, -2,  1, -1, -2]), 
    # ('a', 'c'): array([-2, -1, -1, -3, -1]), 
    # ('a', 'd'): array([-4, -3, -3, -2, -3]), 
    # ('a', 'e'): array([-3, -4, -2, -4, -4]), 
    # ('b', 'c'): array([-1,  1, -2, -2,  1]), 
    # ('b', 'd'): array([-3, -1, -4, -1, -1]), 
    # ('b', 'e'): array([-2, -2, -3, -3, -2]), 
    # ('c', 'd'): array([-2, -2, -2,  1, -2]), 
    # ('c', 'e'): array([-1, -3, -1, -1, -3]), 
    # ('d', 'e'): array([ 1, -1,  1, -2, -1])

    # Count number of negative elements
    counting_dict = {}
    for key in pairs_dict:
        counting_dict[key] = np.sum(np.array((pairs_dict[key])) < 0, axis=0)
    print("counting_dict:", counting_dict)
    # ('a', 'b'): 4,
    # ('a', 'c'): 5,
    # ('a', 'd'): 5, 
    # ('a', 'e'): 5, 
    # ('b', 'c'): 3, 
    # ('b', 'd'): 5, 
    # ('b', 'e'): 5, 
    # ('c', 'd'): 4, 
    # ('c', 'e'): 5, 
    # ('d', 'e'): 3

    # Filter using gamma - the fairness parameter as the thereshold
    edge_dict = {}
    no_edge_dict = {}
    for i in counting_dict:
        if counting_dict[i] >= gamma:
            edge_dict[i] = counting_dict[i]
        else:
            no_edge_dict[i] = counting_dict[i]
    print("no_edge_dict: ", no_edge_dict)
    # ('b', 'c'): 3, 
    # ('d', 'e'): 3
    print("edge_dict: ", edge_dict)
    # ('a', 'b'): 4, 
    # ('a', 'c'): 5, 
    # ('a', 'd'): 5, 
    # ('a', 'e'): 5, 
    # ('b', 'd'): 5, 
    # ('b', 'e'): 5, 
    # ('c', 'd'): 4, 
    # ('c', 'e'): 5
    assert len(edge_dict) + len(no_edge_dict) == (n ** 2 - n) / 2

    # Add edges to the graph
    G = nx.DiGraph()
    for i in edge_dict:
        G.add_edge(str(i[0]), str(i[1]))
    print("G.graph: ", G.edges)
    return G, no_edge_dict
# returns a graph, and the empty edges:(b, c), (d, e)
# (a->b), (a->c), (a->d), (a->e)
#                 (b->d), (b->e)
#                 (c->d), (c->e

def complete_list_of_edges(H: nx.DiGraph, no_edge_dict: Dict) -> nx.DiGraph:
    """
    line 28-48:
    builds graph and for every pair of vertices that are not
    connected, look at common descendants
    If there is a common descendant, 
      add (a,b) edge if a has more descendants
      (b,a) if b has more descendants
    deterministically (say alphabetically) if equal
  
    If there is no common descendant, then there is currently not enough information to order both a,b
    (one of them could still be ordered).
    Args:
  
    Returns: H, a fully connected graph
    """
    descendants_0 = iter([])
    descendants_1 = iter([])
    for key in no_edge_dict:
        assert H.has_edge(key[0], key[1]) is False
        print(
            "(%s, %s) does NOT have an edge, looking at common descendants: "
            % (key[0], key[1])
        )
        descendants_0 = list(H.successors(key[0]))
        descendants_1 = list(H.successors(key[1]))
        print("%s's descendants: " % key[0], descendants_0)
        print("%s's descendants: " % key[1], descendants_1)
        if len(list(set(descendants_0) & set(descendants_1))) == 0:
            has_common_descendants = False
            print(
                "node %s and node %s have no common descendant, not enough info"
                % (key[0], key[1])
            )
        else:
            has_common_descendants = True
            if len(descendants_0) >= len(descendants_1):
                H.add_edge(key[0], key[1])
                print(
                    "node %s has more or equal descendants than %s, adding edge  %s -> %s"
                    % (key[0], key[1], key[0], key[1])
                )
            else:
                H.add_edge(key[1], key[0])
                print(
                    "node %s has more descendants than %s, adding edge  %s -> %s"
                    % (key[1], key[0], key[1], key[0])
                )
    n = len(H.nodes)
    # TODO: what about the edge with not enough info? Fully connected?
    # assert (len(H.edges)==(n**2-n)/2), "H is NOT a fully connected graph"
    return H


def finalize_output(H) -> List:
    """
    line 49-52:
    Compute the condensation graph of H(collapse the strongly connected components into a single vertex)
    Then topologically sort this graph and then output the sorting (Here, every index is a set of vertices)

    Returns: A list of final output ordering
    """
    condensed_DAG = nx.condensation(H)
    # TODO: need to keep track of which nodes gets condensed into one single node, because we need to output an ordering eventually
    output = list(nx.topological_sort(condensed_DAG))
    return output
# Final output ordering: [a,b,c]


def aequitas():
    for i in n_tx_lists:
        n_granularized_tx_lists[i] = granularize(
            n_tx_lists.get(i), starting_timestamp, granularity
        )
    print(n_granularized_tx_lists)

    # TODO: Some data processing and cleaning to get the following simplified_dict
    simplified_dict = {
    1: [Tx(content='a', timestamp=1326244364, bucket = 0), Tx(content='b', timestamp=1326244365, bucket = 0), Tx(content='c', timestamp=1326244366, bucket = 0), Tx(content='e', timestamp=1326244367, bucket = 0), Tx(content='d', timestamp=1326244368, bucket = 0)],
    2: [Tx(content='a', timestamp=1326244364, bucket = 0), Tx(content='c', timestamp=1326244365, bucket = 0), Tx(content='b', timestamp=1326244366, bucket = 0), Tx(content='d', timestamp=1326244367, bucket = 0), Tx(content='e', timestamp=1326244368, bucket = 0)],
    3: [Tx(content='b', timestamp=1326244364, bucket = 0), Tx(content='a', timestamp=1326244365, bucket = 0), Tx(content='c', timestamp=1326244366, bucket = 0), Tx(content='e', timestamp=1326244367, bucket = 0), Tx(content='d', timestamp=1326244368, bucket = 0)], 
    4: [Tx(content='a', timestamp=1326244364, bucket = 0), Tx(content='b', timestamp=1326244365, bucket = 0), Tx(content='d', timestamp=1326244366, bucket = 0), Tx(content='c', timestamp=1326244367, bucket = 0), Tx(content='e', timestamp=1326244368, bucket = 0)], 
    5: [Tx(content='a', timestamp=1326244364, bucket = 0), Tx(content='c', timestamp=1326244365, bucket = 0), Tx(content='b', timestamp=1326244366, bucket = 0), Tx(content='d', timestamp=1326244367, bucket = 0), Tx(content='e', timestamp=1326244368, bucket = 0)]}

    (G, no_edge_dict) = compute_initial_set_of_edges(simplified_dict)
    H = complete_list_of_edges(G, no_edge_dict)
    # finalize_output(H)
    # return


## TESTS
# // Example 1 : simple
# Node 1: [a,b,c,d,e]
# Node 2: [a,b,c,e,d]
# Node 3: [a,b,c,d,e]

# (a->b), (a->c), (a->d), (a->e)
#         (b->c), (b->d), (b->e)
#                 (c->d), (c->e)
#                         (d->e)
# // simple scenario, the graph is complete
# Final output ordering: a->b->c->d->e

# // Example 2: common descendant, and no common descendant
# Node 1: [a,b,c,e,d]
# Node 2: [a,c,b,d,e]
# Node 3: [b,a,c,e,d]
# Node 4: [a,b,d,c,e]
# Node 5: [a,c,b,d,e]

# gamma = 4/5 (to add an edge, you need x<y in 4 nodes)

# (a->b), (a->c), (a->d), (a->e)
#                 (b->d), (b->e)
#                 (c->d), (c->e)

# // b and c dont have an edge but they have a common descendant: e
# // Lets say, we add (b,c) as the edge deterministically
# // d and e dont have an edge but they dont have a common descendant either, i.e. they wont be output yet
# Final output ordering: :a->b->c

# // Example 3: have cycles, look at condensation graph
# Node 1: [b,c,e,a,d]
# Node 2: [b,c,e,a,d]
# Node 3: [a,c,b,d,e]
# Node 4: [a,c,b,d,e]
# Node 5: [e,a,b,c,d]

# gamma = 3/5 (to add an edge, you need x<y in 3 nodes)

# (a->b), (a->c), (a->d),
#                 (b->d), (b->e)
#                 (c->d), (c->e)
#                                (e->a)

# // The graph contains two cycles: a,b,e and a,c,e
# // [a,b,c,e] is the strongly connected component(SCC), they are assumed to be output at the same time
# // we leave the specification up to the implementation (because we don’t consider unfairness within such an SCC)
# Final output ordering:  [a,b,c,e] -> d


def main():
    aequitas()


if __name__ == "__main__":
    main()
