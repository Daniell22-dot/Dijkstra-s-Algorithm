"""
Create the PostgreSQL schema and load the extracted BIM data.

Reads DATABASE_URL from .env (default: postgresql://postgres:postgres@localhost:5433/dijk).

Usage:
    python load_database.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'backend'))

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, '.env'))

from config import Config
from database import db, initialize_database
from services.data_importer import DataImporter

TABLES = ['rooms', 'doors', 'windows', 'floors', 'network_nodes', 'network_edges']


def main():
    print(f'Database: {Config.DATABASE_URL}')
    initialize_database()
    DataImporter().import_all()

    print('\nRow counts')
    for table in TABLES:
        row = db.execute_one(f'SELECT COUNT(*) AS c FROM {table}')
        print(f'  {table:<15} {row["c"]:>5}')

    print('\nSample rooms')
    rows = db.execute_query(
        "SELECT name, floor, type, area FROM rooms ORDER BY floor, name LIMIT 8"
    )
    for row in rows:
        print(f'  {row["floor"]:<7} {row["name"]:<6} {row["type"]:<15} {row["area"]:>8} m2')

    print('\nRoom types')
    rows = db.execute_query(
        "SELECT type, COUNT(*) AS c FROM rooms GROUP BY type ORDER BY c DESC"
    )
    for row in rows:
        print(f'  {row["type"]:<15} {row["c"]:>4}')

    db.close_all_connections()


if __name__ == '__main__':
    main()
