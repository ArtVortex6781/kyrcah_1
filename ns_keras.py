import numpy as np
from keras.layers import Dense, Input, GRU
from keras import Sequential


def change_weights(raw_w: list):
    """changes a list of numbers with 1 axis, btw for game_modelX, x - number of nc
    :param raw_w: raw weights
    """
    base_shapes = [(3, 192), (64, 192), (2, 192), (64, 9), (9,)]
    raw_w = np.array(raw_w)
    weights = []

    st_i = 0
    for tp in base_shapes:
        plus_ind = tp[0] * tp[1] if len(tp) == 2 else tp[0]
        weights.append(raw_w[st_i: st_i + plus_ind].reshape(tp))
        st_i += plus_ind

    return weights


neir_c_1lvl = 64

game_model1 = Sequential([Input((3, 3)),
                          GRU(neir_c_1lvl, activation = "relu"),
                          Dense(9, activation = 'softmax')])

game_model2 = Sequential([Input((3, 3)),
                          GRU(neir_c_1lvl, activation = "relu"),
                          Dense(9, activation = 'softmax')])

game_model1.build(9)
"13,833"
game_model2.build(9)

# print([x.shape for x in game_model1.get_weights()])
# game_model1.summary()

save_model = Sequential([Input((3, 3)),
                         GRU(neir_c_1lvl, activation = "relu"),
                         Dense(9, activation = 'softmax')])
