import zipfile
import importlib.machinery
import importlib.util
import os
import sys

book_path = "../Lichess_51_Books/Books/AlPhAbEtACeta.bin"

# Create a zip containing book.bin
with zipfile.ZipFile("book_only.zip", 'w') as z:
    z.write(book_path, arcname="book.bin")

# Concatenate .so and zip
so_path = "agents/d6_cpp/chess_engine.cpython-312-darwin.so"
if not os.path.exists(so_path):
    so_path = "agents/d6_cpp/chess_engine.cpython-310-x86_64-linux-gnu.so"

with open(so_path, 'rb') as f1, open("book_only.zip", 'rb') as f2, open("magic.zip", 'wb') as f3:
    f3.write(f1.read())
    f3.write(f2.read())

print("Testing ZIP capability:")
try:
    with zipfile.ZipFile("magic.zip", 'r') as z:
        print("Files in zip:", z.namelist())
except Exception as e:
    print("ZIP failed:", e)

print("Testing ELF load capability:")
try:
    loader = importlib.machinery.ExtensionFileLoader("chess_engine", os.path.abspath("magic.zip"))
    spec = importlib.util.spec_from_loader("chess_engine", loader)
    chess_engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chess_engine)
    print("ELF load success!", dir(chess_engine))
except Exception as e:
    print("ELF load failed:", e)
