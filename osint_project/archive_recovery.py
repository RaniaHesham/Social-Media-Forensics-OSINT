def recover_deleted(username):

    return {
        "wayback": f"https://web.archive.org/web/*/{username}",
        "status": "cached snapshots available"
    }