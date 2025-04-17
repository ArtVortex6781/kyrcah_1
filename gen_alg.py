import matplotlib
from deap import base
from deap import creator
from deap import tools
import matplotlib.pyplot as plt
import algelitism
import random
import numpy as np

from classes_for_game import TicTacToe
from ns_keras import game_model1, change_weights, save_model

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

stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("max", np.max)
stats.register("avg", np.mean)

population, logbook = algelitism.eaSimpleElitism(population, toolbox,
                                                 cxpb = P_CROSSOVER,
                                                 mutpb = P_MUTATION,
                                                 ngen = MAX_GENERATIONS,
                                                 halloffame = hof,
                                                 stats = stats,
                                                 verbose = True)

maxFitnessValues, meanFitnessValues = logbook.select("max", "avg")

best = hof.items[0]

plt.plot(maxFitnessValues, color = 'red')
plt.plot(meanFitnessValues, color = 'green')
plt.xlabel('Поколение')
plt.ylabel('Макс/средняя приспособленность')
plt.title('Зависимость максимальной и средней приспособленности от поколения')
plt.show()

save_model.set_weights(change_weights(best))
save_model.save("modelv4_3igr.keras")
