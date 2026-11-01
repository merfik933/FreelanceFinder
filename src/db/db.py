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

    return record_id

def add_record(table, data):
    with connect() as connection:
        return _insert_record(connection, table, data)

def add_records(table, records):
    if not records:
        return []

    with connect() as connection:
        return [_insert_record(connection, table, record) for record in records]

def get_record(table, record_id=None, **filters):
    conditions = []
    parameters = []

    if record_id is not None and record_id >= 0:
        conditions.append("id = ?")
        parameters.append(record_id)

    conditions.extend(f"{column} = ?" for column in filters)
    parameters.extend(filters.values())

    query = f"SELECT * FROM {table}"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if record_id is not None and record_id < 0:
        query += " ORDER BY id DESC LIMIT 1 OFFSET ?"
        parameters.append(-record_id - 1)
    else:
        query += " LIMIT 1"

    with connect() as connection:
        record = connection.execute(query, parameters).fetchone()
        return dict(record) if record is not None else None

def get_records(table, **filters):
    conditions = []
    parameters = []

    conditions.extend(f"{column} = ?" for column in filters)
    parameters.extend(filters.values())

    query = f"SELECT * FROM {table}"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    with connect() as connection:
        return [dict(record) for record in connection.execute(query, parameters).fetchall()]

def clear_table(table):
    with connect() as connection:
        connection.execute(f"DELETE FROM {table}")

def delete_record(table, record_id):
    query = f"DELETE FROM {table} WHERE id = ?"
    with connect() as connection:
        connection.execute(query, (record_id,))
