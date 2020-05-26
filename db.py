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


def select_sales(num_limit=10):
    cursor.execute('SELECT prc_date, prc_description, prc_text '
                   f'FROM promocodes ORDER BY prc_rate DESC LIMIT {num_limit}')
    return cursor.fetchall()


def select_random_collection(num_limit=10):
    cursor.execute('SELECT DISTINCT prc_id FROM prcbooks ORDER BY RANDOM() LIMIT 1')
    prc_id = cursor.fetchone()
    cursor.execute('SELECT prc_description, prc_text FROM promocodes WHERE prc_id = ?', prc_id)
    description_text = cursor.fetchone()
    cursor.execute('SELECT book_link, book_author, book_title FROM books WHERE book_link IN'
                   f'(SELECT book_link FROM prcbooks WHERE prc_id = ?) ORDER BY RANDOM() LIMIT {num_limit}', prc_id)
    return (description_text, cursor.fetchall())


def select_book_by_link(link):
    cursor.execute(f"SELECT prc_id FROM prcbooks WHERE book_link = '{link}'")
    prc_id = cursor.fetchall()
    if prc_id:
        placeholders = ', '.join('?' * len(prc_id))
        cursor.execute(f'SELECT prc_description, prc_text FROM promocodes WHERE prc_id IN ({placeholders})', [id[0] for id in prc_id])
        return cursor.fetchall()
    return False


def select_book_by_title_or_author(message):
    answer = []
    cursor.execute("SELECT book_link, book_title, book_author FROM books WHERE "
                   f"book_author LIKE '{message}%' OR book_title LIKE '{message}%'")
    for book in cursor.fetchall():
        link, title, author = book
        cursor.execute("SELECT prc_description, prc_text FROM promocodes WHERE prc_id IN "
                       f"( SELECT prc_id FROM prcbooks WHERE book_link = '{link}' )")
        description_text = cursor.fetchall()
        answer.append((link, title, author, description_text))
    return answer


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