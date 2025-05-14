from logs import WorkWithDB, ReadDataTables
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('TkAgg')


def fitness_trend_run17():
    """ first """

    fig = plt.figure(figsize = (10, 6))

    with WorkWithDB() as db:
        data = ReadDataTables.fetch_generation_stats(db, 16)

    x = np.arange(len(data))
    y1 = np.array([x["fitness_max"] for x in data])
    y2 = np.array([x["fitness_avg"] for x in data])
    y3 = np.array([x["fitness_min"] for x in data])

    l1, = plt.plot(x, y1, lw = 2, marker = 'o', markersize = 5, markevery = 1, c = 'red')
    l2, = plt.plot(x, y2, lw = 2, marker = 'o', markersize = 5, markevery = 1, c = "blue")
    l3, = plt.plot(x, y3, lw = 2, marker = 'o', markersize = 5, markevery = 1, c = 'g')

    plt.legend((l1, l2, l3), ["fitness_max", "fitness_avg", "fitness_min"], bbox_to_anchor = (0.99, 0.9))

    plt.grid(True, linestyle = '--', alpha = 0.5)
    plt.title("Динамика максимальной, средней и минимальной приспособленности по поколениям")
    plt.xlabel("Поколение")
    plt.ylabel("Приспособленность")

    plt.savefig(r"plots/fitness_trend_run17.png")


def fitness_std_run17():
    """ second """

    fig = plt.figure(figsize = (10, 6))

    with WorkWithDB() as db:
        data = ReadDataTables.fetch_generation_stats(db, 16)

    x = np.arange(len(data))
    y1 = np.array([x["fitness_std"] for x in data])

    l, = plt.plot(x, y1, lw = 2, marker = 'o', markersize = 5, markevery = 1, c = "#791f87")

    plt.legend((l,), ["fitness_std"])

    plt.grid(True, linestyle = '--', alpha = 0.5)
    plt.title("Динамика стандартного отклонения по поколениям")
    plt.xlabel("Поколение")
    plt.ylabel("Значения СКО")

    plt.savefig(r"plots/fitness_std_run17.png")
