import os

import pymysql


def get_connection():
    password = os.getenv("DB_PASSWORD")
    if not password:
        raise RuntimeError("Set the DB_PASSWORD environment variable before starting the server.")

    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=password,
        database=os.getenv("DB_NAME", "coursedb"),
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )
