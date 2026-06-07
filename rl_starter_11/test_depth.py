import sys
sys.path.insert(0, "agents/d6_cpp")
import chess_engine_d6_han as chess_engine
import numpy as np

engine = chess_engine.SearchEngine()
engine.init("")
