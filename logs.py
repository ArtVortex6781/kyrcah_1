from __future__ import annotations
import sqlite3 as sq
from typing import Callable
from functools import wraps
from types import FunctionType
from datetime import datetime


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
    def try_work_decor(cls):
        """ A basic decorator that applies to a class and decorates all functions without __ to work with exceptions
        :param cls: class to be decorated
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> object:
                db = None
                for arg in args:
                    if isinstance(arg, WorkWithDB):
                        db = arg
                        break
                if db is None:
                    raise ValueError("WorkWithDB instance not found among arguments")
                try:
                    res = func(*args, **kwargs)
                    db.con.commit()
                    return res
                except sq.Error as e:
                    db.con.rollback()
                    run_id = getattr(db, "current_run_id", None)
                    try:
                        db.cur.execute(
                            "INSERT INTO errors(run_id, timestamp, error_message, traceback) VALUES(?, ?, ?, ?)",
                            (run_id, datetime.now().isoformat(), str(e), repr(e.__traceback__)))
                        db.con.commit()
                    except Exception:
                        print("Failed to log error:", e)
                    db.__exit__(e.__class__, e, e.__traceback__)

            return wrapper

        for name, fnc in cls.__dict__.items():
            if name.startswith("__"):
                continue
            elif isinstance(fnc, classmethod):
                original_func = fnc.__func__
                wrapped_func = decorator(original_func)
                setattr(cls, name, classmethod(wrapped_func))

            elif isinstance(fnc, staticmethod):
                original_func = fnc.__func__
                wrapped_func = decorator(original_func)
                setattr(cls, name, staticmethod(wrapped_func))

            elif isinstance(fnc, FunctionType):
                setattr(cls, name, decorator(fnc))

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
        """Adds a record to Runs and returns the ID of that record"""
        obj_db.cur.execute("INSERT INTO runs (time_run, seed) VALUES (?, ?)", (time_run, seed))

        obj_db.current_run_id = obj_db.cur.lastrowid
        return obj_db.cur.lastrowid

    @staticmethod
    def insert_generation(obj_db: WorkWithDB, run_id: int, population_size: int, p_crossover: float, p_mutation: float,
                          low: float, up: float, eta: float, generations: int, fame_size: int) -> int:
        """ Adds a record to generations and returns the new ga_id """
        obj_db.cur.execute(
            """INSERT INTO generations
               (run_id, population_size, p_crossover, p_mutation, low, up, eta, generations, fame_size)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, population_size, p_crossover, p_mutation, low, up, eta, generations, fame_size)
        )
        return obj_db.cur.lastrowid

    @staticmethod
    def insert_model_config(obj_db: WorkWithDB, run_id: int, gru_units: int, gru_activation: str) -> int:
        """ Adds a record to model_configs and returns the new config_id """
        obj_db.cur.execute(
            "INSERT INTO model_configs (run_id, gru_units, gru_activation) VALUES (?, ?, ?)",
            (run_id, gru_units, gru_activation)
        )
        return obj_db.cur.lastrowid

    @staticmethod
    def insert_generation_stats(obj_db: WorkWithDB, gen_id: int, config_id: int, fitness_max: float, fitness_avg: float,
                                fitness_min: float, fitness_std: float) -> int:
        """ Adds a record to generation_stats and returns the new stat_id """
        obj_db.cur.execute(
            """INSERT INTO generation_stats
               (gen_id, config_id, fitness_max, fitness_avg, fitness_min, fitness_std)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (gen_id, config_id, fitness_max, fitness_avg, fitness_min, fitness_std)
        )
        return obj_db.cur.lastrowid

    @staticmethod
    def insert_hall_of_fame(obj_db: WorkWithDB, gen_id: int, config_id: int, fitness: float, chromosome: str) -> int:
        """ Adds a record to hall_of_fame and returns the new hof_id """
        obj_db.cur.execute(
            "INSERT INTO hall_of_fame (gen_id, config_id, fitness, chromosome) VALUES (?, ?, ?, ?)",
            (gen_id, config_id, fitness, chromosome)
        )
        return obj_db.cur.lastrowid

    @staticmethod
    def insert_game(obj_db: WorkWithDB, run_id: int, result: str, moves: int, timestamp: str) -> int:
        """ Adds a record to games and returns the new game_id """
        obj_db.cur.execute(
            "INSERT INTO games (run_id, result, moves, timestamp) VALUES (?, ?, ?, ?)",
            (run_id, result, moves, timestamp)
        )
        return obj_db.cur.lastrowid

    @staticmethod
    def insert_error(obj_db: WorkWithDB, run_id: int | None, timestamp: str, error_message: str, traceback: str) -> int:
        """ Adds a record to errors and returns the new error_id """
        obj_db.cur.execute(
            "INSERT INTO errors (run_id, timestamp, error_message, traceback) VALUES (?, ?, ?, ?)",
            (run_id, timestamp, error_message, traceback)
        )
        return obj_db.cur.lastrowid


@WorkWithDB.try_work_decor
class ReadDataTables:
    """ read data from tables"""
    pass
