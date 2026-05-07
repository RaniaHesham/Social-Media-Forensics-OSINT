from github_api import get_repo_contributors


_contributors_cache = {}


def _contributors_for(repo_full_name):
    if repo_full_name in _contributors_cache:
        return _contributors_cache[repo_full_name]
    contribs = set([c.lower() for c in get_repo_contributors(repo_full_name) if c])
    _contributors_cache[repo_full_name] = contribs
    return contribs


def _users_collaborate_via_contrib(u1, u2, p1, p2, max_repos_per_user=20):
    """
    True collaboration signal:
    - u2 is a contributor on any repo in u1's repo list, OR
    - u1 is a contributor on any repo in u2's repo list.
    """
    u1_l = str(u1).lower()
    u2_l = str(u2).lower()

    repos1 = [r for r in (p1.get("repos_full") or []) if r]
    repos2 = [r for r in (p2.get("repos_full") or []) if r]

    repos1 = repos1[:max_repos_per_user]
    repos2 = repos2[:max_repos_per_user]

    for repo in repos1:
        if u2_l in _contributors_for(repo):
            return True
    for repo in repos2:
        if u1_l in _contributors_for(repo):
            return True
    return False


def build_relationships(profiles):

    relationships = []
    users = list(profiles.keys())

    for i in range(len(users)):
        for j in range(i + 1, len(users)):

            u1 = users[i]
            u2 = users[j]
            p1 = profiles[u1]
            p2 = profiles[u2]

            score = 0
            reasons = []

            loc1 = p1.get("location")
            loc2 = p2.get("location")
            if loc1 and loc2 and loc1.strip().lower() == loc2.strip().lower():
                score += 40
                reasons.append("same_location")

            repos1 = set(p1.get("repos", []))
            repos2 = set(p2.get("repos", []))
            if _users_collaborate_via_contrib(u1, u2, p1, p2):
                score += 30
                reasons.append("shared_repo")

            following1 = set(p1.get("following_list", []))
            following2 = set(p2.get("following_list", []))

            if u2 in following1 or u1 in following2:
                score += 35
                reasons.append("follows")

            if score > 0:
                relationships.append({
                    "from": u1,
                    "to": u2,
                    "score": score,
                    "reasons": list(set(reasons))
                })

    return relationships