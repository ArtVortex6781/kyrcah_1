import sqlite3 as sq


class AllLogs:
    """class for working with all log tables, the Singeton"""
    __obj = None

    def __new__(cls, *args, **kwargs):
        if cls.__obj is None:
            cls.__obj = super().__new__(cls)
        return cls.__obj

    def __init__(self):
        """init connect to database"""
        try:
            self._ocn_con = sq.connect("database_logs/db1.db")
            self._ocn_cur = self._ocn_con.cursor()
        except sq.Error as e:
            print("error work with db")
            raise e

    def close_connection(self):
        try:
            self._ocn_con.commit()
        except sq.Error as e:
            if self._ocn_con:
                self._ocn_con.rollback()
            print(e, "error close")
        finally:
            if self._ocn_con:
                self._ocn_con.close()

    def reset_table_runs(self):
        try:
            self._ocn_cur.executescript("""
            BEGIN;
            DROP TABLE IF EXIST runs;
            CREATE TABLE IF NOT EXISTS runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_run TEXT,
            seed INTEGER,
            )
            """)
            self._ocn_con.commit()
        except sq.Error:
            if self._ocn_con:
                self._ocn_con.rollback()
