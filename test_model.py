from pathlib import Path
from keras.models import load_model
from classes_for_game import TicTacToe
from keras import Sequential

MODELS_DIR = Path(__file__).resolve().parent / "models"

model: Sequential = load_model(MODELS_DIR / "modelv7_5igr.keras")
game = TicTacToe()
game.game_with_nc(model)
