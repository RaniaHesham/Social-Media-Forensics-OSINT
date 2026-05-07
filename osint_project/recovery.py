import requests
from bs4 import BeautifulSoup
import json
import os

CACHE_FILE = "cache.json"


def get_wayback_snapshots(url):
    """
    Returns a list of snapshot URLs for the given page.

    Strategy:
    - First try Wayback "available" endpoint (fast, may return only closest).
    - If that yields nothing, fall back to the CDX API to discover snapshots.
    """
    available_api = "https://archive.org/wayback/available"
    snapshots = []

    try:
        res = requests.get(available_api, params={"url": url}, timeout=10).json()
        closest = res.get("archived_snapshots", {}).get("closest", {}).get("url")
        if closest:
            snapshots.append(closest)
    except:
        pass

    if snapshots:
        return snapshots

    # Fallback: CDX snapshot discovery (returns timestamps)
    cdx_api = "https://web.archive.org/cdx/search/cdx"
    try:
        cdx = requests.get(
            cdx_api,
            params={
                "url": url,
                "output": "json",
                "fl": "timestamp,original",
                "filter": "statuscode:200",
                "collapse": "digest",
                "limit": 5
            },
            timeout=12
        ).json()
    except:
        return []

    # First row is header
    for row in cdx[1:]:
        try:
            ts, original = row[0], row[1]
            snapshots.append(f"https://web.archive.org/web/{ts}/{original}")
        except:
            continue

    return snapshots


def extract_archived_content(archive_url):
    try:
        html = requests.get(archive_url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        return {
            "title": soup.title.string.strip() if soup.title and soup.title.string else "",
            "text": soup.get_text(separator=" ", strip=True)[:1000]
        }

    except Exception as e:
        return {"error": str(e)}


def compare_content(current, archived):
    current_text = str(current)
    archived_text = str(archived)

    return {
        "current_length": len(current_text),
        "archived_length": len(archived_text),
        "difference": abs(len(current_text) - len(archived_text))
    }

def get_deleted_repos(username, current_repos):
    if not os.path.exists(CACHE_FILE):
        return []

    if not current_repos:
        return []

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except:
        return []

    history = cache.get(username, [])

    if len(history) < 2:
        return []

    all_seen = set()
    for snapshot in history:
        for repo in snapshot.get("repos", []):
            all_seen.add(repo)

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

    seen_names, seen_full = _to_names_and_full(all_seen)
    cur_names, cur_full = _to_names_and_full(current_repos)

    deleted_full_raw = sorted(list(seen_full - cur_full))
    deleted_full = [fn for fn in deleted_full_raw if fn.split("/", 1)[1] not in cur_names]
    deleted_names = sorted(list(seen_names - cur_names))
    deleted = deleted_full + [n for n in deleted_names if n not in {fn.split("/", 1)[1] for fn in deleted_full}]

    return deleted