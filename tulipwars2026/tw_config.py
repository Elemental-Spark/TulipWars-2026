# TulipWars 2026 defaults.
# A separate /user/tulipwars_user_config.py overrides these values so that
# Tulip World package updates never erase a player's server configuration.
SERVER_URL = "https://elementalspark.com/tulipwars2026/api.php"
GAME_VERSION = "0.1.8"
GAME_TITLE = "TulipWars 2026"
WORLD_PACKAGE = "tulipwars2026"
WORLD_AUTHOR = ""
CALLSIGN_PREFIX = "TULIP"
HEARTBEAT_MS = 60000


def _load_user_config():
    global SERVER_URL, WORLD_AUTHOR
    try:
        import tulip
        rooted = tulip.root_dir() + "user/tulipwars_user_config.py"
    except Exception:
        rooted = "/user/tulipwars_user_config.py"
    paths = (
        rooted,
        "/user/tulipwars_user_config.py",
        "../tulipwars_user_config.py",
        "tulipwars_user_config.py",
    )
    for path in paths:
        try:
            namespace = {}
            with open(path, "r") as handle:
                exec(handle.read(), namespace)
            if namespace.get("SERVER_URL"):
                SERVER_URL = namespace["SERVER_URL"]
            if "WORLD_AUTHOR" in namespace:
                WORLD_AUTHOR = namespace["WORLD_AUTHOR"]
            return
        except Exception:
            pass


_load_user_config()
