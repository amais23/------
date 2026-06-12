import urllib.request
import os
import zipfile

raw_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/research/data/raw"
os.makedirs(raw_dir, exist_ok=True)

players = [
    "Carlsen", "Kasparov", "Fischer", "Karpov", "Anand",
    "Alekhine", "Capablanca", "Tal", "Smyslov", "Spassky",
    "Petrosian", "Botvinnik", "Euwe", "Lasker", "Steinitz",
    "Kramnik", "Topalov", "Caruana", "Nakamura", "Aronian",
    "Gelfand", "Ivanchuk", "Svidler", "Polgar", "Leko",
    "Morozevich", "Karjakin", "Mamedyarov", "Radjabov", "Giri",
    "So", "Ding", "Nepomniachtchi", "VachierLagrave", "Firouzja"
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for player in players:
    # Check if the PGN file already exists to avoid redundant download
    pgn_dest = f"{raw_dir}/{player}.pgn"
    if os.path.exists(pgn_dest):
        print(f"{player}.pgn already exists, skipping.")
        continue
        
    url = f"https://www.pgnmentor.com/players/{player}.zip"
    zip_dest = f"{raw_dir}/{player}.zip"
    print(f"Downloading {player}.zip from {url}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(zip_dest, 'wb') as f:
                f.write(response.read())
        print(f"Downloaded {player}.zip ({os.path.getsize(zip_dest) / 1024:.1f} KB)")
        
        # Extract the zip
        print(f"Extracting {player}.zip...")
        with zipfile.ZipFile(zip_dest, 'r') as zip_ref:
            zip_ref.extractall(raw_dir)
            
        os.remove(zip_dest)
        print(f"Extraction completed. Zip file deleted.")
    except Exception as e:
        print(f"Failed to download or extract {player}: {e}")
        if os.path.exists(zip_dest):
            os.remove(zip_dest)
