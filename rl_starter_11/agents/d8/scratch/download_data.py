import urllib.request
import os
import zipfile

raw_dir = "/Users/Shared/西洋棋代理人/rl_starter_11/agents/d8/research/data/raw"
os.makedirs(raw_dir, exist_ok=True)

urls = {
    "Carlsen": "https://www.pgnmentor.com/players/Carlsen.zip",
    "Kasparov": "https://www.pgnmentor.com/players/Kasparov.zip",
    "Fischer": "https://www.pgnmentor.com/players/Fischer.zip",
    "Karpov": "https://www.pgnmentor.com/players/Karpov.zip",
    "Anand": "https://www.pgnmentor.com/players/Anand.zip",
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for player, url in urls.items():
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
