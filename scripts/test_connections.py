import asyncio
from nexus_ai.config import get_settings
from nexus_ai.patient_finance.mongodb import init_mongodb
from nexus_ai.db.session import engine
from nexus_ai.patient_finance.arize_tracing import init_tracing

async def test():
    print('Testing Arize...')
    init_tracing()
    print('Testing MongoDB...')
    await init_mongodb()
    print('Testing Cloud SQL...')
    conn = engine.connect()
    print('Connected Cloud SQL!')
    conn.close()
    print('All good!')

asyncio.run(test())
