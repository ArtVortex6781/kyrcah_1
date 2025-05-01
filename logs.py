import sqlite3 as sq


class WorkWithDB:
    """The main class where the database is connected and closed, etc.,
    The class also implements the Singleton и the class is also a contextual manager"""
    __obj = None

    def __new__(cls, *args, **kwargs):
        """Singleton and start connect to db"""
        if cls.__obj is None:
            cls.__obj = object.__new__(cls)
            try:
                cls.__obj.con = sq.connect("database_logs/db1.db")
                cls.__obj.cur = cls.__obj.con.cursor()
            except sq.Error as e:
                print("error connect with db")
                raise e
        return cls.__obj

    def __enter__(self):
        """return self object"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """commit and close db or rollback and close the connection and del object who work"""
        try:
            if exc_type:
                self.con.rollback()
            else:
                self.con.commit()
        finally:
            self.con.close()
            self.__class__.__obj = None

    def close_connection(self):
        """close connection"""
        try:
            self.con.commit()
        except sq.Error as e:
            if self.con:
                self.con.rollback()
            print(e, "error close")
        finally:
            if self.con:
                self.con.close()


class ResetTables:

    @staticmethod
    def reset_table_runs(obj_db: WorkWithDB):
        """reset or create table runs"""
        try:
            obj_db.cur.executescript("""
            BEGIN;
            DROP TABLE IF EXISTS runs;
            CREATE TABLE IF NOT EXISTS runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_run TEXT,
            seed INTEGER
            )
            """)
            obj_db.con.commit()
        except sq.Error:
            if obj_db.con:
                obj_db.con.rollback()
