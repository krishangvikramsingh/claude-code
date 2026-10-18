import secrets
from pathlib import Path

from srp import config
from srp.seed import build_sample_platform, load_demo_data
from srp.server import create_server
from srp.store import SqliteStore


def open_platform():
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    store = SqliteStore(config.DB_PATH)
    if not store.is_empty():
        from srp.service import Platform
        return Platform(store=store)
    password = config.ADMIN_PASSWORD or secrets.token_urlsafe(12)
    platform, _ = build_sample_platform(store, password, config.ADMIN_EMAIL)
    if config.LOAD_DEMO_DATA:
        load_demo_data(platform)
    if not config.ADMIN_PASSWORD:
        print(f"First run: administrator {config.ADMIN_EMAIL} created with generated password: {password}")
    return platform


def main():
    platform = open_platform()
    server = create_server(platform)
    print(f"Student Recommendation Platform running at http://{config.HOST}:{config.PORT}/ (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")


if __name__ == "__main__":
    main()
