import os
import pymysql


def connect():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "alzikrayat"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def query(sql, values=(), one=False):
    with connect() as db:
        with db.cursor() as cursor:
            cursor.execute(sql, values)
            if sql.lstrip().upper().startswith("SELECT"):
                return cursor.fetchone() if one else cursor.fetchall()
            return cursor.lastrowid
