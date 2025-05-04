import sqlite3 as sq
from typing import Callable
from functools import wraps


class WorkWithDB:
    """The main class where the database is connected and closed, etc.,
    The class also implements the Singleton и the class is also a contextual manager"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton and start connect to db"""
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            try:
                cls._instance.con = sq.connect("database_logs/db1.db")
                cls._instance.cur = cls._instance.con.cursor()
            except sq.Error as e:
                print("error connect with db")
                raise e
        return cls._instance

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
            type(self)._instance = None

    def close_connection(self):
        """ run exit if you have connection """
        if hasattr(self, "con") and self.con:
            self.__exit__(None, None, None)
        else:
            print("Соединение уже закрыто")

    @staticmethod
    def try_work_decor(cls: object) -> object:
        """ A basic decorator that applies to a class and decorates all functions without __ to work with exceptions
        :param cls: class to be decorated
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(arg1, arg2, *args, **kwargs) -> object:
                db = arg2 if isinstance(arg2, WorkWithDB) else arg1
                try:
                    return func(arg1, arg2, *args, **kwargs)
                except sq.Error as e:
                    db.con.rollback()
                    db.__exit__(e.__class__, e, e.__traceback__)

            return wrapper

        for name, func in cls.__dict__.items():
            if not name.startswith("__") and callable(func):
                setattr(cls, name, decorator(func))

        return cls


@WorkWithDB.try_work_decor
class ResetTables:
    """ reset or create tables and similar actions with tables, that is, here is the structure of tabels"""
    __tables = {"runs": """CREATE TABLE IF NOT EXISTS runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_run TEXT,
            seed INTEGER
            )""",
                "generations": """ CREATE TABLE IF NOT EXISTS generations (
            ga_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            population_size INTEGER,
            p_crossover REAL,
            p_mutation REAL,
            low REAL,
            up REAL,
            eta REAL,
            generations INTEGER,
            fame_size INTEGER
            )""",
                "model_configs": """ CREATE TABLE IF NOT EXISTS model_configs (
            config_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id	INTEGER,
            gru_units INTEGER,
            gru_activation TEXT
            )""",
                "generation_stats": """ CREATE TABLE IF NOT EXISTS generation_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            gen_id INTEGER,
            config_id INTEGER,
            fitness_max REAL,
            fitness_avg REAL,
            fitness_min REAL,
            fitness_std REAL
            )""",
                "hall_of_fame": """ CREATE TABLE IF NOT EXISTS hall_of_fame (
            hof_id INTEGER PRIMARY KEY AUTOINCREMENT,
            gen_id INTEGER,
            config_id INTEGER,
            fitness REAL,
            chromosome TEXT
            )""",
                "games": """ CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                result TEXT,
                moves INTEGER,
                timestamp TEXT
                )""",
                "errors": """ CREATE TABLE IF NOT EXISTS errors (
                error_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                timestamp TEXT,
                error_message TEXT,
                traceback TEXT
                )"""}

    @classmethod
    def reset_or_create_tables(cls, obj_db: WorkWithDB, name_table: str):
        """reset and create the tables that are valid and available in the class
        :param obj_db: object WorkWithDB
        :param name_table: table name, which must be permissible
        """
        if name_table not in cls.__tables:
            print("Нету такой таблицы")
            return
        obj_db.cur.executescript(f"""
            BEGIN;
            DROP TABLE IF EXISTS {name_table};
            {cls.__tables[name_table]};
            """)
        obj_db.con.commit()

    @classmethod
    def reset_all_tables(cls, obj_db: WorkWithDB):
        """reset and create the tables that are valid and available in the class"""
        for table in cls.__tables:
            cls.reset_or_create_tables(obj_db, table)


@WorkWithDB.try_work_decor
class RecordingInTable:
    """ writing data to tables """

    @staticmethod
    def insert_run(obj_db: WorkWithDB, time_run: str, seed: int) -> int:
        "Adds a record to Runs and returns the ID of that record"
        obj_db.cur.execute(f"INSERT INTO runs (time_run, seed) VALUES ({time_run}, {seed})")


class ReadDataTables:
    """ read data from tables"""
    pass


