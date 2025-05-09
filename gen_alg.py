from datetime import datetime
import matplotlib
import numpy.random
from deap import base
from deap import creator
from deap import tools
import matplotlib.pyplot as plt
import algelitism
import random
import numpy as np
from logs import WorkWithDB, RecordingInTable, ResetTables

from classes_for_game import TicTacToe
from ns_keras import game_model1, change_weights, save_model, neir_c_1lvl

matplotlib.use("TkAgg")

# константы генетического алгоритма
LENGTH_CHROM = 8_709

LOW = -1.0
UP = 1.0
ETA = 22

POPULATION_SIZE = 56  # количество индивидуумов в популяции
P_CROSSOVER = 0.9  # вероятность скрещивания
P_MUTATION = 0.15  # вероятность мутации индивидуума
MAX_GENERATIONS = 46  # максимальное количество поколений
HALL_OF_FAME_SIZE = 3

GRU_UNITS = neir_c_1lvl
GRU_ACTIVATION = "relu"

SEED = random.getrandbits(32)
random.seed(SEED)
numpy.random.seed(SEED)

hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

creator.create("FitnessMax", base.Fitness, weights = (1.0,))
creator.create("Individual", list, fitness = creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("randomWeight", random.uniform, LOW, UP)
toolbox.register("individualCreator", tools.initRepeat, creator.Individual, toolbox.randomWeight, LENGTH_CHROM)
toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)

population = toolbox.populationCreator(n = POPULATION_SIZE)


def get_score(individual):
    game_model1.set_weights(change_weights(individual))

    pole = TicTacToe()
    reward = pole.game_2nc(game_model1)
    return reward,


toolbox.register("evaluate", get_score)
toolbox.register("select", tools.selTournament, tournsize = 3)
toolbox.register("mate", tools.cxSimulatedBinaryBounded, low = LOW, up = UP, eta = ETA)
toolbox.register("mutate", tools.mutPolynomialBounded, low = LOW, up = UP, eta = ETA, indpb = 1.0 / LENGTH_CHROM)

with WorkWithDB() as db:
    time_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    run_id = RecordingInTable.insert_run(db, time_run, SEED)
    ga_id = RecordingInTable.insert_generation(
        db, run_id, POPULATION_SIZE, P_CROSSOVER, P_MUTATION, LOW, UP, ETA, MAX_GENERATIONS, HALL_OF_FAME_SIZE
    )
    config_id = RecordingInTable.insert_model_config(db, run_id, GRU_UNITS, GRU_ACTIVATION)

    stats = tools.Statistics(lambda ind: ind.fitness.values[0])
    stats.register("avg", lambda x: sum(x) / len(x))
    stats.register("min", min)
    stats.register("max", max)
    stats.register("std", lambda x: (sum((xi - sum(x) / len(x)) ** 2 for xi in x) / len(x)) ** 0.5)

    population, logbook = algelitism.eaSimpleElitism(population, toolbox,
                                                     cxpb = P_CROSSOVER,
                                                     mutpb = P_MUTATION,
                                                     ngen = MAX_GENERATIONS,
                                                     stats = stats,
                                                     halloffame = hof,
                                                     verbose = True)

    for gen_data in logbook:
        RecordingInTable.insert_generation_stats(
            db, gen_id = ga_id, config_id = config_id,
            fitness_max = gen_data["max"],
            fitness_avg = gen_data["avg"],
            fitness_min = gen_data["min"],
            fitness_std = gen_data["std"]
        )

    for ind in hof:
        fitness = ind.fitness.values[0]
        chromosome = str(ind)
        RecordingInTable.insert_hall_of_fame(db, gen_id = ga_id, config_id = config_id, fitness = fitness,
                                             chromosome = chromosome)

    maxFitnessValues, meanFitnessValues = logbook.select("max", "avg")

    best = hof.items[0]

    plt.plot(maxFitnessValues, color = 'red')
    plt.plot(meanFitnessValues, color = 'green')
    plt.xlabel('Поколение')
    plt.ylabel('Макс/средняя приспособленность')
    plt.title('Зависимость максимальной и средней приспособленности от поколения')
    plt.show()

    save_model.set_weights(change_weights(best))
    save_model.save(r"models\modelv6_3igr.keras")
