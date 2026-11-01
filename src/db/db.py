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

def _insert_record(connection, current_table, current_data):
    relation_records = {
        key: value for key, value in current_data.items()
        if isinstance(value, (list, tuple))
    }
    record_data = {
        key: value for key, value in current_data.items()
        if not isinstance(value, (list, tuple))
    }

    if record_data:
        columns = ', '.join(record_data.keys())
        placeholders = ', '.join(['?'] * len(record_data))
        query = f"INSERT INTO {current_table} ({columns}) VALUES ({placeholders})"
        cursor = connection.execute(query, tuple(record_data.values()))
    else:
        cursor = connection.execute(f"INSERT INTO {current_table} DEFAULT VALUES")

    record_id = cursor.lastrowid

    for relation_table, values in relation_records.items():
        query = f"INSERT INTO {relation_table} VALUES (?, ?)"
        connection.executemany(query, ((record_id, value) for value in values))

def add_record(table, data):
    with connect() as connection:
        _insert_record(connection, table, data)

def add_records(table, records):
    if not records:
        return

    with connect() as connection:
        for record in records:
            _insert_record(connection, table, record)

def delete_record(table, record_id):
    query = f"DELETE FROM {table} WHERE id = ?"
    with connect() as connection:
        connection.execute(query, (record_id,))