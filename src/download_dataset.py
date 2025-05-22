import os
import requests

base_url = "https://api.github.com/repos/tatsu-lab/alpaca_eval/contents/results "
local_path = "../model_results"

os.makedirs(local_path, exist_ok=True)

response = requests.get(base_url)
if response.status_code == 200:
    files = response.json()
    for file in files:
        file_name = file["name"]
        file_url = file["download_url"]
        file_path = os.path.join(local_path, file_name)
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded: {file_name}")
else:
    print(f"Failed to fetch file list. Status code: {response.status_code}")