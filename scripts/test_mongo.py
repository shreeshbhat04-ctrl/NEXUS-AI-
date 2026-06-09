import asyncio
import logging
from nexus_ai.patient_finance.mongodb import init_mongodb

logging.basicConfig(level=logging.DEBUG)

async def test():
    print('Connecting to MongoDB...')
    await init_mongodb()
    print('Connected to MongoDB!')

if __name__ == '__main__':
    asyncio.run(test())
