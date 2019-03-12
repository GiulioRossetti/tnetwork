import networkx as nx
from tnetwork.utils.community_utils import jaccard
from tnetwork.DCD.computing_coms_by_sn import *


def _match_communities_according_to_com(dynComSN, matchesGraph):
    """

    :param dynComSN:
    :param matchesGraph:
    :return:
    """
    #find affiliations in the graph of matching
    node2comID = best_partition(matchesGraph)
    #for each "node" (of this network of affiliations)
    for (t,c),cID in node2comID.items():
        #create an ID
        newComID = "DC_"+str(cID)
        #if this Id is already present, means that 2 affiliations of the SAME timestep are merged, modified the affiliations accordingly
        if newComID in dynComSN._snapshots[t].inv:
            dynComSN._snapshots[t].inv[newComID]=dynComSN._snapshots[t].inv[newComID].union(c)
            del dynComSN._snapshots[t][c]
        else: #replace the ID of the (local) community by the ID of the (global) community
            dynComSN._snapshots[t][c]=newComID #add DC_ to avoid confusion with already assigned com ID






def _build_matches_graph(partitions, match_function=jaccard, threshold=0.3):
    graph = nx.Graph()
    coms = partitions.affiliations()

    allComs = set()
    for t in coms:  # for each date taken in chronological order
       for c in coms[t]:
           allComs.add((t,c))


    for com1 in allComs:
        for com2 in allComs:
            if com1!=com2: #if not same community
                score = match_function(com1[1], com2[1])
                if score>=threshold:
                    commonNodes = len(com1[1] & com2[1])
                    identityPreservation = commonNodes / len(com1[1]) * commonNodes / len(com2[1])

                    graph.add_edge(com1,com2,weight=score)#the weight is used such as the louvain algorihtm applied afterwards uses it (not sure it does)

    return graph

def match_survival_graph(dynNetSN, CDalgo="louvain", match_function=jaccard, threshold=0.3):
    """
    Community detection by survival graph matching

    This method is based on falkowsky et al.[1]. It first detect communities in each snapshot, then try to match
    any community with any other one in any other snapshot, constituting a survival graph.
    A community detection algorithm is then applied on this survival graph, yielding dynamic communities.

    [1]Falkowski, T., Bartelheimer, J., & Spiliopoulou, M. (2006, December).
    Mining and visualizing the evolution of subgroups in social networks.
    In Proceedings of the 2006 IEEE/WIC/ACM International Conference on Web Intelligence (pp. 52-58). IEEE Computer Society.

    :param dynNetSN: a dynamic network
    :param CDalgo: community detection to apply at each step. Can be a function returning a clustering, or the string "louvain" or "smoothedLouvain
    :param match_function: a function that gives a matching score between two communities (two sets of nodes). Default: jaccard
    :param threshold: a threshold for match_function below which communities are not matched
    :return: DynCommunitiesSN
    """
    if CDalgo == "smoothedLouvain":
        dynPartitions = smoothed_louvain(dynNetSN)
    elif CDalgo == "louvain":
        dynPartitions = CD_each_step(dynNetSN, best_partition)
    else:
        dynPartitions = CD_each_step(dynNetSN, CDalgo)

    matchesGraph = _build_matches_graph(dynPartitions, match_function, threshold)

    _match_communities_according_to_com(dynPartitions, matchesGraph)

    dynPartitions.create_standard_event_graph()

    return dynPartitions
