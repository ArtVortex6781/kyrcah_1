from deap import tools
from deap.algorithms import varAnd


def eaSimpleElitism(population, toolbox, cxpb, mutpb, ngen, stats=None,
             halloffame=None, verbose=__debug__, callback=None):
    """Перелеланный алгоритм eaSimple с элементом элитизма"""

    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    # Evaluate the individuals with an invalid fitness
    # Оцените людей с недопустимой пригодностью
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)

    hof_size = len(halloffame.items) if halloffame.items else 0

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(invalid_ind), **record)
    if verbose:
        print(logbook.stream)

    # Begin the generational process
    # Начать процесс генерации
    for gen in range(1, ngen + 1):
        # Select the next generation individuals
        # Выберите людей следующего поколения
        offspring = toolbox.select(population, len(population) - hof_size) # эвалюция без особей которые в зале славы

        # Vary the pool of individuals
        # Варьируйте пул лиц
        offspring = varAnd(offspring, toolbox, cxpb, mutpb)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        offspring.extend(halloffame.items)

        # Update the hall of fame with the generated individuals
        # Обновите зал славы сгенерированными людьми
        if halloffame is not None:
            halloffame.update(offspring)

        # Replace the current population by the offspring
        # Заменить текущую популяцию потомками
        population[:] = offspring

        # Append the current generation statistics to the logbook
        # Добавление статистики текущего поколения в бортовой журнал
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        if verbose:
            print(logbook.stream)

        if callback:
            callback[0](*callback[1])

    return population, logbook
