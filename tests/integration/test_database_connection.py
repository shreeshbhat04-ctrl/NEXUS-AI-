from sqlalchemy import text

from nexus_ai.config import get_settings
from nexus_ai.db.bootstrap import init_database
from nexus_ai.db.session import SessionLocal


def main() -> None:
    settings = get_settings()
    init_database()
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    print("DATABASE", settings.resolved_database_url)
    print("BRAIN_GATEWAY_MODE", settings.brain_gateway_mode)
    print("STATUS ok")


if __name__ == "__main__":
    main()
