import logging
from sqlalchemy import text

from nexus_ai.config import get_settings
from nexus_ai.db.session import engine
from nexus_ai.db.models import Base

logger = logging.getLogger(__name__)

def init_database() -> None:
    settings = get_settings()
    
    with engine.begin() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("Ensured pgvector extension is installed.")
        except Exception as e:
            logger.warning(f"Failed to create pgvector extension. It might already exist or the user lacks permissions: {e}")
            
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("SQLAlchemy tables created.")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise
