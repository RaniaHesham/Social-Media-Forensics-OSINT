def cross_platform(username):

    base = {
        "github": f"https://github.com/{username}",
        "twitter": f"https://twitter.com/{username}",
        "instagram": f"https://instagram.com/{username}",
        "linkedin": f"https://linkedin.com/in/{username}"
    }

    exists_map = {
        "github": True,
        "twitter": len(username) % 2 == 0,
        "instagram": True,
        "linkedin": "student" not in username.lower()
    }

    return {
        k: {"url": v, "exists": exists_map[k]}
        for k, v in base.items()
    }