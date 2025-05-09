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
        if not hasattr(self, "con") or not self.con or type(self)._instance is None:
            print("Соединение уже закрыто")
            return
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
        if hasattr(self, "con") and self.con and type(self)._instance is not None:
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
                    raise ValueError("WorkWithDB экземпляр не найден среди аргументов")
                try:
                    res = func(*args, **kwargs)
                    db.con.commit()
                    return res
                except sq.Error as e:
                    db.con.rollback()
                    try:
                        db.cur.execute(
                            "INSERT INTO errors (run_id, timestamp, error_message, traceback) VALUES (?, ?, ?, ?)",
                            (getattr(db.cur, "current_run_id", None), datetime.now().isoformat(), str(e),
                             repr(e.__traceback__)))
                        db.con.commit()
                    except Exception as all_e:
                        print("Failed to log error:", all_e)
                        raise
                    db.__exit__(e.__class__, e, e.__traceback__)
                    raise e

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

    @staticmethod
    def dict_output(func):
        """ A decorator for methods that perform select queries.
        func returns an SQ instance. Cursor a wrapper transforms the data into a more readable form.
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> list[dict]:
            cur: sq.Cursor = func(*args, **kwargs)
            rows = cur.fetchall()
            cols = [col[0] for col in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        return wrapper


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

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_all_runs(obj_db: WorkWithDB) -> sq.Cursor:
        """ return a list of all launches (runs): - run_id, time_run, seed """

        return obj_db.cur.execute("""
        SELECT * FROM runs
        """)

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_generations_for_run(obj_db: WorkWithDB, run_id: int) -> sq.Cursor:
        """ Return all records from generations for this run_id:
        ga_id, run_id, population_size, p_crossover, p_mutation, low, up, eta, generations, fame_size """

        return obj_db.cur.execute("""
        SELECT * FROM generations
        WHERE run_id == ?
        """, (run_id,))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_model_configs_for_run(obj_db: WorkWithDB, run_id: int) -> sq.Cursor:
        """ Return all model configurations (model_configs) for this run_id:
        config_id, run_id, gru_units, gru_activation
        """

        return obj_db.cur.execute("""
        SELECT * FROM model_configs
        WHERE run_id == ?
        """, (run_id,))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_generation_stats(obj_db: WorkWithDB, gen_id: int) -> sq.Cursor:
        """ Return Generation Statistics (generation_stats) for this gen_id:
        stat_id, gen_id, config_id, fitness_max, fitness_avg, fitness_min, fitness_std
        """

        return obj_db.cur.execute("""
        SELECT * FROM generation_stats
        WHERE gen_id == ?
        """, (gen_id,))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_hall_of_fame(obj_db: WorkWithDB, gen_id: int) -> sq.Cursor:
        """ Return the Hall of Fame (hall_of_fame) for this gen_id:
         hof_id, gen_id, config_id, fitness, chromosome
        """

        return obj_db.cur.execute("""
        SELECT * FROM hall_of_fame
        WHERE gen_id == ?
        """, (gen_id,))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_games_for_run(obj_db: WorkWithDB, run_id: int) -> sq.Cursor:
        """ return the results of the games for the run_id:
        game_id, run_id, result, moves, timestamp
        """

        return obj_db.cur.execute("""
        SELECT * FROM games
        WHERE run_id == ?
        """, (run_id,))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_errors_for_run(obj_db: WorkWithDB, run_id: int) -> sq.Cursor:
        """return errors for this run_id:
        - error_id, run_id, timestamp, error_message, traceback
        """

        return obj_db.cur.execute("""
        SELECT * FROM errors
        WHERE run_id == ?
        """, (run_id,))

    @staticmethod
    @WorkWithDB.dict_output
    def summary_fitness_trend(obj_db: WorkWithDB, run_id: int) -> sq.Cursor:
        """ for each generation of a given run_id return:
        - generations.ga_id,
        - generations.generations (generation number),
        - generation_stats.fitness_max,
        - generation_stats.fitness_avg
        """
        return obj_db.cur.execute("""
        SELECT generations.ga_id, generations.generations, generation_stats.fitness_max, generation_stats.fitness_avg
        FROM generations
        JOIN generation_stats ON generations.ga_id = generation_stats.gen_id
        WHERE generations.run_id == ?
        """, (run_id,))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_run_overview(obj_db: WorkWithDB, run_id: int) -> sq.Cursor:
        """ returns summarized run information
          run id start time seed;
          number of generations ga parameters (p_crossover, p_mutation etc.);
          total statistics of games: wins, draws, losses, total games;
        """
        return obj_db.cur.execute("""SELECT runs.run_id, runs.time_run, runs.seed,  
        generations.population_size, generations.p_crossover, generations.p_mutation, 
        generations.eta, generations.low, generations.up,
        games.result, games.moves, games.timestamp
        FROM runs
        JOIN generations ON runs.run_id == generations.run_id
        JOIN games ON runs.run_id == games.run_id
        WHERE runs.run_id == ?
        """, (run_id, ))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_generation_detailed(obj_db: WorkWithDB, ga_id: int) -> sq.Cursor:
        """ Returns the details of a specific generation:
          Generation and statistics parameters (fitness, etc.);
          Top 3 Chromosomes from the Fitness Hall of Fame in descending order;
        """
        return obj_db.cur.execute(""" SELECT generations.population_size, generations.p_crossover, 
        generations.p_mutation, generations.eta, generations.low, generations.up,
        generation_stats.fitness_max, generation_stats.fitness_avg, 
        generation_stats.fitness_max, generation_stats.fitness_avg,
        hall_of_fame.fitness
        FROM generations
        JOIN generation_stats ON generations.ga_id == generation_stats.gen_id
        JOIN hall_of_fame ON hall_of_fame.gen_id == generations.ga_id
        WHERE generations.ga_id == ?
        ORDER BY hall_of_fame.fitness DESC
        LIMIT 3
        """, (ga_id, ))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_config_performance(obj_db: WorkWithDB, config_id: int) -> sq.Cursor:
        """ Returns the performance of a single model configuration across generations:
           fitness_max, fitness_avg, etc. for each iteration (gen_id);
        """
        return obj_db.cur.execute(""" SELECT generation_stats.fitness_max, generation_stats.fitness_avg, 
        generation_stats.fitness_max, generation_stats.fitness_avg,
        model_config.gru_units, model_config.gru_activation
        FROM generation_stats
        JOIN model_configs ON generation_stats.config_id == model_configs.config_id
        WHERE model_configs.config_id == ?
        """, (config_id, ))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_error_summary(obj_db: WorkWithDB, run_id: int) -> sq.Cursor:
        """ Returns a list of errors that occurred in this run:
            timestamp, error message, traceback
        """
        return obj_db.cur.execute(""" SELECT timestamp, error_message, traceback FROM errors
        WHERE run_id == ?
        """, (run_id, ))

    @staticmethod
    @WorkWithDB.dict_output
    def fetch_game_statistics(obj_db: WorkWithDB, run_id: int) -> sq.Cursor:
        """ Returns game statistics from the run:
            Game ID, result, number of moves;
            as well as aggregates: average number of moves, total wins, draws, losses;
        """
        return obj_db.cur.execute(""" SELECT game_id, result, moves, timestamp FROM games
        WHERE run_id == ?
        """, (run_id, ))
