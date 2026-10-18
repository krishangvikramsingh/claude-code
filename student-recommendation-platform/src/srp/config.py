import os


def setting(name, default):
    return os.environ.get("SRP_" + name, default)


HOST = setting("HOST", "127.0.0.1")
PORT = int(setting("PORT", "8000"))
DB_PATH = setting("DB_PATH", "data/platform.db")
SESSION_MINUTES = int(setting("SESSION_MINUTES", "30"))
ADMIN_EMAIL = setting("ADMIN_EMAIL", "admin@platform.in")
ADMIN_PASSWORD = setting("ADMIN_PASSWORD", "")
LOAD_DEMO_DATA = setting("DEMO_DATA", "1") == "1"
