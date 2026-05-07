import networkx as nx


def norm(x, max_x):
    return x / max_x if max_x > 0 else 0


def compute_risk(users_profiles, G, repo_changes, cross_platform):

    risks = {}

    max_followers = max([u.get("followers", 0) for u in users_profiles.values()], default=1)
    max_repos = max([u.get("public_repos", 0) for u in users_profiles.values()], default=1)

    degree = nx.degree_centrality(G) if len(G) > 0 else {}
    betweenness = nx.betweenness_centrality(G) if len(G) > 1 else {}
    pagerank = nx.pagerank(G) if len(G) > 1 else {}

    for user, profile in users_profiles.items():

        followers = profile.get("followers", 0)
        following = profile.get("following", 0)
        repos = profile.get("public_repos", 0)

        identity = (
            (1 - norm(followers, max_followers)) * 0.35 +
            (1 - norm(repos, max_repos)) * 0.35 +
            (1 if not profile.get("bio") or profile["bio"] in ["No bio", ""] else 0.1)
        )



        ratio = followers / (following + 1)
        social_risk = 1 if ratio < 0.5 else 0.3



        cp = cross_platform.get(user, {})
        cp_risk = 0.5 if len(cp) <= 2 else 0.1



        changes = repo_changes.get(user, {})
        activity = (
            len(changes.get("added", [])) +
            len(changes.get("deleted", []))
        ) / 10
        activity = min(activity, 1)



        influence = (
            degree.get(user, 0) * 0.4 +
            betweenness.get(user, 0) * 0.3 +
            pagerank.get(user, 0) * 0.3
        )



        score = (
            identity * 0.4 +
            social_risk * 0.2 +
            cp_risk * 0.15 +
            activity * 0.15 -
            influence * 0.1
        )


        score = (score + 1) * 50


        score = max(0, min(100, score))

        risks[user] = round(score, 2)

    return risks