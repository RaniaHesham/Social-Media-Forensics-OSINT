import requests
import json
import os
import time

CACHE_FILE = "cache.json"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "OSINT-Forensics-System"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def extract_profile(username):
    url = f"https://api.github.com/users/{username}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code == 200:
            d = r.json()

            repos_data = get_user_repos(username)
            following_data = get_following(username)
            followers_data = get_followers(username)

            repos_full = [
                repo.get("full_name")
                for repo in repos_data
                if isinstance(repo, dict) and repo.get("full_name")
            ]

            return {
                "username": d.get("login"),
                "bio": d.get("bio") or "No bio",
                "location": d.get("location"),
                "followers": d.get("followers", 0),
                "following": d.get("following", 0),
                "public_repos": d.get("public_repos", 0),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
                "repos": [r["name"] for r in repos_data if isinstance(r, dict)],
                "repos_full": repos_full,
                "following_list": [u["login"] for u in following_data if isinstance(u, dict)],
                "followers_list": [u["login"] for u in followers_data if isinstance(u, dict)],
            }

        return _empty_profile(username)

    except:
        return _empty_profile(username)


def _empty_profile(username):
    return {
        "username": username,
        "bio": "Error/Not found",
        "location": None,
        "followers": 0,
        "following": 0,
        "public_repos": 0,
        "created_at": None,
        "updated_at": None,
        "repos": [],
        "repos_full": [],
        "following_list": [],
        "followers_list": [],
    }


def get_user_repos(username):
    url = f"https://api.github.com/users/{username}/repos?per_page=100"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code == 200:
            return r.json()

        return []

    except:
        return []


def get_following(username):
    url = f"https://api.github.com/users/{username}/following?per_page=100"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code == 200:
            return r.json()

        return []

    except:
        return []


def get_followers(username):
    url = f"https://api.github.com/users/{username}/followers?per_page=100"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code == 200:
            return r.json()

        return []

    except:
        return []


def get_repo_contributors(full_name):
    """
    Returns a list of contributor logins for a repo (public data).
    full_name format: owner/repo
    """
    if not full_name or "/" not in str(full_name):
        return []

    url = f"https://api.github.com/repos/{full_name}/contributors?per_page=100&anon=false"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return [u.get("login") for u in data if isinstance(u, dict) and u.get("login")]
        return []
    except:
        return []

def cross_platform(username):

    import subprocess

    url_display = {
        "github":    f"https://github.com/{username}",
        "gitlab":    f"https://gitlab.com/{username}",
        "bitbucket": f"https://bitbucket.org/{username}",
        "instagram": f"https://instagram.com/{username}",
        "twitter":   f"https://twitter.com/{username}",
        "facebook":  f"https://facebook.com/{username}",
    }

    api_platforms = {
        "github":    f"https://api.github.com/users/{username}",
        "gitlab":    f"https://gitlab.com/api/v4/users?username={username}",
        "bitbucket": f"https://api.bitbucket.org/2.0/users/{username}",
    }

    result = {}

    for platform, url in api_platforms.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)

            if platform == "github":
                exists = r.status_code == 200
            elif platform == "gitlab":
                data = r.json()
                exists = isinstance(data, list) and len(data) > 0
            elif platform == "bitbucket":
                exists = r.status_code == 200
            else:
                exists = False

            result[platform] = {
                "url": url_display[platform],
                "exists": exists
            }

        except:
            result[platform] = {
                "url": url_display[platform],
                "exists": False
            }

    try:
        proc = subprocess.run(
            ["sherlock", username, "--print-found", "--timeout", "10"],
            capture_output=True, text=True, timeout=60
        )

        output = proc.stdout.lower()

        for platform in ["instagram", "twitter", "facebook"]:
            found = platform in output and url_display[platform].lower() in output
            result[platform] = {
                "url": url_display[platform],
                "exists": found
            }

    except:
        for platform in ["instagram", "twitter", "facebook"]:
            result[platform] = {
                "url": url_display[platform],
                "exists": False
            }

    return result


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_snapshot(username, repos):

    cache = load_cache()

    repo_names = [
        r.get("name")
        for r in repos
        if isinstance(r, dict) and r.get("name")
    ]

    if username not in cache:
        cache[username] = []

    cache[username].append({
        "timestamp": time.time(),
        "repos": repo_names
    })

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)


def detect_changes(username):

    cache = load_cache()
    history = cache.get(username, [])

    if len(history) < 2:
        return {
            "status": "no_history",
            "added": [],
            "deleted": []
        }

    def _to_names_and_full(items):
        names = set()
        full = set()
        for it in items or []:
            if not it:
                continue
            s = str(it).strip()
            if not s:
                continue
            if "/" in s:
                full.add(s)
                names.add(s.split("/", 1)[1])
            else:
                names.add(s)
        return names, full

    old_items = history[-2].get("repos", [])
    new_items = history[-1].get("repos", [])

    old_names, old_full = _to_names_and_full(old_items)
    new_names, new_full = _to_names_and_full(new_items)

    added_names = sorted(list(new_names - old_names))
    deleted_names = sorted(list(old_names - new_names))

    return {
        "added": added_names,
        "deleted": deleted_names,
        "previous_count": len(old_names),
        "current_count": len(new_names)
    }