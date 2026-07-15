# Run from the Tulip REPL after entering the package folder:
#   cd('tulipwars2026')
#   import tw_setup
#   tw_setup.configure()


def configure():
    print("TulipWars 2026 anonymous relay setup")
    print("Enter the complete HTTPS URL ending in /api.php")
    print("Example: https://example.com/tulipwars2026/api.php")
    url = input().strip()
    if not url.startswith("https://") or not url.endswith("api.php"):
        print("That URL does not look complete. Nothing was changed.")
        return False
    text = "SERVER_URL = %r\nWORLD_AUTHOR = ''\n" % url
    try:
        import tulip
        rooted = tulip.root_dir() + "user/tulipwars_user_config.py"
    except Exception:
        rooted = "/user/tulipwars_user_config.py"
    paths = (rooted, "/user/tulipwars_user_config.py", "../tulipwars_user_config.py")
    tried = {}
    for path in paths:
        if path in tried:
            continue
        tried[path] = True
        try:
            with open(path, "w") as handle:
                handle.write(text)
            print("Saved anonymous relay configuration to", path)
            print("Return to the user folder and run('tulipwars2026')")
            return True
        except Exception:
            pass
    print("Could not write tulipwars_user_config.py")
    return False
