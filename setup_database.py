from database import get_connection


def ensure_unique_index(connection, table, columns, index_name):
    quoted_table = f"`{table}`"
    quoted_columns = ", ".join(f"`{column}`" for column in columns)
    column_list = ", ".join(f"`{column}`" for column in columns)

    with connection.cursor() as cursor:
        cursor.execute(f"SHOW INDEX FROM {quoted_table} WHERE Key_name=%s", (index_name,))
        if cursor.fetchone():
            return

        cursor.execute(
            f"SELECT {column_list} FROM {quoted_table} "
            f"WHERE {' AND '.join(f'`{column}` IS NOT NULL' for column in columns)} "
            f"GROUP BY {column_list} HAVING COUNT(*) > 1 LIMIT 1"
        )
        duplicate = cursor.fetchone()
        if duplicate:
            raise RuntimeError(
                f"Cannot create {index_name}: duplicate values exist in {table}."
            )

        cursor.execute(
            f"ALTER TABLE {quoted_table} ADD UNIQUE KEY `{index_name}` ({quoted_columns})"
        )


def setup_database():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE admininfo MODIFY password VARCHAR(255) NULL")
            cursor.execute("ALTER TABLE stndinfo MODIFY password VARCHAR(255) NULL")
        connection.commit()

        ensure_unique_index(connection, "courseinfo", ("course_id",), "uq_courseinfo_id")
        ensure_unique_index(connection, "staffinfo", ("staff_id",), "uq_staffinfo_id")
        ensure_unique_index(connection, "stndinfo", ("uname",), "uq_stndinfo_uname")
        ensure_unique_index(
            connection,
            "enrollinfo",
            ("stnd_id", "course_id"),
            "uq_enrollinfo_student_course",
        )
        connection.commit()
        print("Database setup complete.")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    setup_database()
