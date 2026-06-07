import sys
sys.path.insert(0, "agents/d6_cpp")
import chess_engine
import numpy as np

chess_engine.init("")

def make_obs():
    # just an empty observation to trick solve(), wait rebuild_fen_from_observation needs real board
    pass

