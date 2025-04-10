from keras.models import load_model
from classes_for_game import TicTacToe
from keras import Sequential

model: Sequential = load_model("modelv3_3igr.keras")
game = TicTacToe()
game.game_with_nc(model)

# print(model.get_weights())
