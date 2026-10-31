import sqlite3
import configparser
from contextlib import contextmanager

config = configparser.ConfigParser()
config.read('config.ini')
DB_PATH = config.get('Database', 'path')

@contextmanager
def connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        with connection:
            yield connection
    finally:
        connection.close()

def add_record(table, data):
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    with connect() as connection:
        connection.execute(query, tuple(data.values()))

def delete_record(table, record_id):
    query = f"DELETE FROM {table} WHERE id = ?"
    with connect() as connection:
        connection.execute(query, (record_id,))