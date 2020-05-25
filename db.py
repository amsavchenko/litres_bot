import sqlite3
from sqlite3 import Error

db_name = 'litres_bot.db'
conn = sqlite3.connect(db_name)
cursor = conn.cursor()


# def post_sql_query(sql_query):
#     with sqlite3.connect(db_name) as con:
#         cursor = con.cursor()
#         try:
#             cursor.execute(sql_query)
#         except Error:
#             pass
#         result = cursor.fetchall()
#         return result

# def insert(table: str, column_values: dict):
#     columns = ', '.join(column_values.keys())
#     values = [tuple(column_values.values())]
#     placeholders = ', '.join('?' * len(column_values.keys()))
#     cursor.executemany(
#         f"INSERT into {table} "
#         f"({columns})"
#         f"VALUES ({placeholders}) ",
#         values
#     )
#     conn.commit()


def insert(table: str, values: list):
    placeholders = ', '.join('?' * len(values[0]))
    cursor.executemany(
        f"INSERT INTO {table} VALUES ({placeholders})", values
    )
    conn.commit()


def _init_db():
    with open('create_db.sql', 'r') as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()


def table_exists(table_name):
    cursor.execute("SELECT name FROM sqlite_master  "
                   f"WHERE type='table'AND name='{table_name}'")
    return bool(cursor.fetchone())


def check_db_exist():
    cursor.execute("SELECT name FROM sqlite_master  "
                   "WHERE type='table'AND name='promocodes'")
    table_exists = cursor.fetchall()
    if not table_exists:
        _init_db()


check_db_exist()