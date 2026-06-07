import os
import importlib.machinery
import importlib.util

so_path = "test_model.zip"

loader = importlib.machinery.ExtensionFileLoader("chess_engine", os.path.abspath(so_path))
spec = importlib.util.spec_from_loader("chess_engine", loader)
chess_engine = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(chess_engine)
    print("Success!", dir(chess_engine))
except Exception as e:
    print("Failed!", e)
