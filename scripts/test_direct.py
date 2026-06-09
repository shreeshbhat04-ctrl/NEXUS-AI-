import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from google.cloud.sql.connector import Connector, IPTypes
import pg8000

async def test_mongo():
    print('Testing MongoDB...')
    client = AsyncIOMotorClient('mongodb+srv://sreeshhb_db_user:30GwdxzGppQNmiwa@cluster0.j6oez1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0', serverSelectionTimeoutMS=5000)
    try:
        await client.admin.command('ping')
        print('MongoDB Connected!')
    except Exception as e:
        print(f'MongoDB Failed: {e}')

def test_cloud_sql():
    print('Testing Cloud SQL...')
    connector = Connector()
    try:
        conn = connector.connect(
            "mindful-hull-496817-q3:us-central1:nexusai",
            "pg8000",
            user="postgres",
            password="Nexusai@123!",
            db="postgres",
            ip_type=IPTypes.PUBLIC,
        )
        print('Cloud SQL Connected!')
        conn.close()
    except Exception as e:
        print(f'Cloud SQL Failed: {e}')

if __name__ == '__main__':
    test_cloud_sql()
    asyncio.run(test_mongo())
