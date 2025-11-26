import os
from collections import defaultdict
import json

DATA_DIR = "gutenberg_books"

index = defaultdict(set)

for filename in os.listdir(DATA_DIR):
    if filename.endswith(".txt"):
        with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8", errors="ignore") as f:
            words = f.read().lower().split()
            for w in set(words):
                index[w].add(filename)
with open("index.json", "w") as f:
    json.dump({k:list(v) for k,v in index.items()}, f)