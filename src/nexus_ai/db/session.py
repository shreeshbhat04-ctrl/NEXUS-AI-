from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nexus_ai.config import get_settings

settings = get_settings()

if settings.cloud_sql_connection_name:
    from google.cloud.sql.connector import Connector, IPTypes
    import pg8000
    
    # We instantiate the connector lazily to avoid module load-time deadlocks
    _connector = None
    
    def getconn() -> pg8000.dbapi.Connection:
        global _connector
        if _connector is None:
            _connector = Connector()
            
        conn: pg8000.dbapi.Connection = _connector.connect(
            settings.cloud_sql_connection_name,
            "pg8000",
            user=settings.cloud_sql_user,
            password=settings.cloud_sql_password,
            db=settings.cloud_sql_database,
            ip_type=IPTypes.PUBLIC,
        )
        return conn

    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
else:
    engine = create_engine(
        settings.get_database_url(),
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
