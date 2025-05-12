from keras import Sequential
from random import choice
from numpy import array, argmax


class Cell:

    def __init__(self, start_v):
        self.__value = start_v

    def __bool__(self):
        return self.__value == 0

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value: int):
        self.__value = value


class TicTacToe:
    FREE_CELL = 45  # свободная клетка
    FIRST_NC = 2  # крестик (1nc - человек)
    SECOND_NC = 3  # нолик (2nc - компьютер)

    def __init__(self):
        self.__pole = tuple(tuple(Cell(self.FREE_CELL) for _ in range(3)) for _ in range(3))

    def __getitem__(self, item: tuple):
        return self.__pole[item[0]][item[1]].value

    def __setitem__(self, item: tuple, value: int):
        self.__pole[item[0]][item[1]].value = value

    @property
    def pole(self):
        return self.__pole

    def __rand_cl(self):
        """get random cell"""
        return choice([(i, j) for i in range(3) for j in range(3) if self[i, j] == self.FREE_CELL])

    def __check_rows(self, value):
        return any(all(y.value == value for y in x) for x in self.pole)

    def __check_cols(self, value):
        return any(all(self[j, i] == value for j in range(3)) for i in range(3))

    def __check_diagonal(self, value):
        return all(self[i, i] == value for i in range(3)) or all(self[x, 2 - x] == value for x in range(3))

    @property
    def is_first_win(self):
        return self.__check_rows(self.FIRST_NC) or self.__check_cols(self.FIRST_NC) or self.__check_diagonal(
            self.FIRST_NC)

    @property
    def is_second_win(self):
        return self.__check_rows(self.SECOND_NC) or self.__check_cols(self.SECOND_NC) or self.__check_diagonal(
            self.SECOND_NC)

    @property
    def is_draw(self):
        return not self.is_first_win and not self.is_second_win and all(
            self[i, j] != self.FREE_CELL for i in range(3) for j in range(3))

    def __bool__(self):
        return not any((self.is_draw, self.is_first_win, self.is_second_win))

    def __help_for_predict(self, nc: Sequential):
        """predict transform"""
        xz_val = argmax(nc.predict(array([y.value for x in self.__pole for y in x]).reshape(1, 3, 3), verbose = 0))
        return xz_val // 3, xz_val % 3

    def reset_pole(self):
        self.__init__()

    def game_2nc(self, nc1: Sequential, nc2: Sequential | None = None, count_games: int = 3) -> int:
        """for GA with one or two nc
        :param nc1: нс которая оценивается
        :param nc2: нс или алг для оценки
        :param count_games: кол-во игр для оценки
        """
        reward = 0
        for _ in range(count_games):
            self.reset_pole()
            flag_win = 1  # 1 - norm win, 0 - win rand
            count_help = 0
            rew_fire = 0
            while self:
                i1, j1 = self.__help_for_predict(nc1)
                if self[i1, j1] != self.FREE_CELL:
                    count_help += 2
                    flag_win = 0
                    self[self.__rand_cl()] = self.FIRST_NC
                    if not self:
                        break
                else:
                    self[i1, j1] = self.FIRST_NC
                    rew_fire += 1

                if not self:
                    break

                if nc2 is not None:
                    i2, j2 = self.__help_for_predict(nc2)
                    if self[i2, j2] in (self.FIRST_NC, self.SECOND_NC):
                        self[self.__rand_cl()] = self.SECOND_NC
                    else:
                        self[i2, j2] = self.SECOND_NC
                else:
                    self[self.__rand_cl()] = self.SECOND_NC

            reward += rew_fire - count_help * 8
            if self.is_first_win:
                if flag_win == 1:
                    reward += 6 + rew_fire
            elif self.is_draw:
                reward -= 5
            else:
                reward -= 10

        return reward

    def show(self):
        print()
        print("_" * 50)
        for x in self.__pole:
            for y in x:
                if y.value == self.FIRST_NC:
                    print(' ' * 10, '|#|', end = '')
                elif y.value == self.SECOND_NC:
                    print(' ' * 10, '|0|', end = '')
                else:
                    print(' ' * 10, '|Пусто|', end = '')
            print('\n', "_" * 50)
        print()

    def game_with_nc(self, nc: Sequential):
        """test play with nc"""
        while self:
            i1, j1 = self.__help_for_predict(nc)
            if self[i1, j1] == self.FREE_CELL:
                self[i1, j1] = self.FIRST_NC
            print(f"xod nc - ({i1}, {j1})")
            self.show()
            if not self:
                break

            i, j = map(int, input("vvod: ").split())
            self[i, j] = self.SECOND_NC

        self.show()

        if self.is_first_win:
            print("nc win")
        elif self.is_draw:
            print("none win")
        else:
            print("ez win")
