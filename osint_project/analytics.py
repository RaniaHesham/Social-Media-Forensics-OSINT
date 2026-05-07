from itertools import combinations
import networkx as nx


def build_intelligence(users_data):

    relations = []
    scores = {}

    users = list(users_data.keys())

    for u, data in users_data.items():
        scores[u] = (
            data.get("followers", 0) * 2 +
            data.get("repos", 0) * 3
        )

    for u1, u2 in combinations(users, 2):

        d1 = users_data[u1]
        d2 = users_data[u2]

        weight = 0

        bio1 = d1.get("bio", "").lower().split()
        bio2 = d2.get("bio", "").lower().split()

        if bio1 and bio2:
            weight += len(set(bio1) & set(bio2))

        if d1.get("location") and d1.get("location") == d2.get("location"):
            weight += 3

        if weight == 0:
            weight = 1

        relations.append((
            u1,
            u2,
            {
                "weight": weight,
                "type": "semantic-link"
            }
        ))

    return relations, scores


def calculate_centrality(G):

    return nx.degree_centrality(G)