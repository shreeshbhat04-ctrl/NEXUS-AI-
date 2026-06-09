import sys
import os

# Add src to the path so we can import nexus_ai
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from nexus_ai.db.session import engine
from nexus_ai.db.models import Base

def init_db():
    print("Initializing Cloud SQL database schema...")
    try:
        # Create all tables defined in models.py
        Base.metadata.create_all(engine)
        print("✅ Successfully generated tables in Cloud SQL!")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")

if __name__ == "__main__":
    init_db()
