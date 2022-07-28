import os
import pathlib

import dotenv

dotenv.load_dotenv(os.path.join(pathlib.Path(__file__).parent.parent.absolute(), '.env'))

DB_SCHEMA = os.environ.get('DB_SCHEMA')
SQLITE_DB = os.environ.get('SQLITE_DB_NAME')
POSTGRE_SETTINGS = {
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('PORT'),
}
