import networkx as nx
from networkx.algorithms import community
import matplotlib.pyplot as plt


def compute_sna(G):
    if G is None or len(G.nodes) == 0:
        return {
            "degree": {},
            "betweenness": {},
            "closeness": {},
            "pagerank": {}
        }
    return {
        "degree": nx.degree_centrality(G),
        "betweenness": nx.betweenness_centrality(G),
        "closeness": nx.closeness_centrality(G),
        "pagerank": nx.pagerank(G)
    }


def visualize_graph(G, output_path="report/network_graph.png"):
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import networkx as nx

    if G is None or len(G.nodes) == 0:
        print("Graph is empty")
        return

    plt.figure(figsize=(14, 10), facecolor="white")
    ax = plt.gca()
    ax.set_facecolor("white")

    pos = nx.kamada_kawai_layout(G)
    pos = {node: (x * 2.0, y * 2.0) for node, (x, y) in pos.items()}

    node_sizes = [1800 + 500 * G.degree(n) for n in G.nodes]

    nx.draw_networkx_nodes(
        G, pos,
        node_size=node_sizes,
        node_color="#1F6FEB",
        alpha=0.9
    )

    color_map = {
        "same_location": "#F78166",
        "shared_repo": "#3FB950",
        "follows": "#D29922",
    }

    edge_colors = []
    for u, v, d in G.edges(data=True):
        reason = d.get("reason", "")
        color = "#8B949E"
        for key, col in color_map.items():
            if key in reason:
                color = col
                break
        edge_colors.append(color)

    nx.draw_networkx_edges(
        G, pos,
        width=2.0,
        edge_color=edge_colors,
        alpha=0.7
    )

    nx.draw_networkx_labels(
        G, pos,
        font_size=8,
        font_color="black",
        font_weight="bold"
    )

    edge_labels = {(u, v): d.get("reason", "") for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=edge_labels,
        font_size=7,
        font_color="#333333"
    )

    patches = [
        mpatches.Patch(color="#F78166", label="Same Location"),
        mpatches.Patch(color="#3FB950", label="Shared Repo"),
        mpatches.Patch(color="#D29922", label="Follows"),
    ]
    plt.legend(handles=patches, loc="upper left",
               facecolor="white", labelcolor="black", fontsize=9)

    plt.title("OSINT Relationship Graph", fontsize=16,
              color="black", pad=20)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Graph saved to: {output_path}")


def build_graph(users_profiles, relationships=None):
    import networkx as nx
    from networkx.algorithms import community

    G = nx.Graph()
    users = list(users_profiles.keys())

    for user in users:
        G.add_node(user)

    if relationships:
        for r in relationships:
            u1 = r.get("from")
            u2 = r.get("to")
            reason = " + ".join(r.get("reasons", ["connected"]))
            if u1 and u2:
                G.add_edge(u1, u2, reason=reason)


    try:
        comms = list(community.greedy_modularity_communities(G))
        community_count = len(comms)
    except:
        community_count = 1

    return {
        "graph": G,
        "metrics": compute_sna(G),
        "communities": community_count
    }