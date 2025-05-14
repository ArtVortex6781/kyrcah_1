from keras.models import load_model
from classes_for_game import TicTacToe
from keras import Sequential

model: Sequential = load_model(r"models\modelv7_5igr.keras")
# model2: Sequential = load_model(r"models\modelv8_5igr.keras")
game = TicTacToe()
game.game_with_nc(model)
# game.game_nc_with_nc(model2, model)
