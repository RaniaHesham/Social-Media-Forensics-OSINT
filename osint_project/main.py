import json
import os

from github_api import (
    extract_profile,
    get_user_repos,
    save_snapshot,
    detect_changes,
    cross_platform
)

from graph_engine import build_graph, compute_sna, visualize_graph
from risk_engine import compute_risk
from recovery import get_wayback_snapshots, get_deleted_repos
from relationship_engine import build_relationships

print("OSINT SYSTEM STARTED")

users = input("Enter usernames (comma separated): ")
users = [u.strip() for u in users.split(",") if u.strip()]

profiles = {}
repo_changes = {}
cross_map = {}

for u in users:

    profile = extract_profile(u)
    repos = get_user_repos(u)

    save_snapshot(u, repos)
    changes = detect_changes(u)
    cross = cross_platform(u)

    profiles[u] = profile
    repo_changes[u] = changes
    cross_map[u] = cross

    print("\nUSER:", u)
    print(profile)

relationships = build_relationships(profiles)

print("\nRELATIONSHIP ANALYSIS")
for r in relationships:
    print(r)

result = build_graph(profiles, relationships)
G = result["graph"]

print("\nGRAPH ANALYSIS")
print(f"Nodes: {len(G.nodes)}")
print(f"Edges: {len(G.edges)}")
print(f"Communities: {result['communities']}")

os.makedirs("report", exist_ok=True)
visualize_graph(G, "report/network_graph.png")

metrics = compute_sna(G)

print("\nCENTRALITY SCORES")
print(json.dumps(metrics, indent=4))

risk = compute_risk(profiles, G, repo_changes, cross_map)

print("\nRISK SCORES")
for user, score in risk.items():
    print(f"{user} -> Risk: {score}/100")

print("\nCROSS PLATFORM CHECK")

for user, links in cross_map.items():
    print(f"\n{user}:")
    for k, v in links.items():
        print(f"  {k}: {v}")

print("\nWAYBACK RECOVERY")

recovery_data = {}

for u in users:
    url = f"https://github.com/{u}"
    snaps = get_wayback_snapshots(url)

    current_repos = [r.get("name") for r in get_user_repos(u) if isinstance(r, dict)]
    deleted = get_deleted_repos(u, current_repos)

    recovery_data[u] = {
        "snapshots": len(snaps),
        "deleted_repos": deleted
    }

    print(f"\n{u}: {len(snaps)} snapshots")
    if deleted:
        print(f"  DELETED REPOS: {deleted}")
    else:
        print(f"  No deleted repos detected")

report = {
    "users": profiles,
    "relationships": relationships,
    "risk_scores": risk,
    "graph": {
        "nodes": len(G.nodes),
        "edges": len(G.edges),
        "communities": result["communities"]
    },
    "metrics": metrics,
    "recovery": recovery_data
}

with open("report/osint_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=4)

print("\nDONE - FULL REPORT GENERATED")
print("Saved at: report/osint_report.json")
print("Graph saved at: report/network_graph.png")