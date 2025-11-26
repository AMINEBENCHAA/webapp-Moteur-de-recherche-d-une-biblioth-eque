import os
import json
import networkx as nx
import pickle  # utiliser pickle pour la sérialisation

DATA_DIR = "gutenberg_books"
JACCARD_THRESHOLD = 0.03   # tu peux augmenter si RAM faible

# Charger l'index
with open("index.json", encoding="utf-8") as f:
    index = json.load(f)

# Liste des livres
books = [f for f in os.listdir(DATA_DIR) if f.endswith(".txt")]

# Précharger les sets de mots par livre
def load_book_words(book):
    with open(os.path.join(DATA_DIR, book), encoding="utf-8", errors="ignore") as f:
        return set(f.read().lower().split())

print("⏳ Chargement des livres...")
book_words = {book: load_book_words(book) for book in books}

# Créer le graphe
G = nx.Graph()
for b in books:
    G.add_node(b)

print("🔗 Construction des arêtes (Jaccard)...")

for i in range(len(books)):
    for j in range(i+1, len(books)):
        b1 = books[i]
        b2 = books[j]

        w1 = book_words[b1]
        w2 = book_words[b2]

        inter = len(w1 & w2)
        union = len(w1 | w2)

        if union == 0:
            continue

        jaccard = inter / union

        if jaccard >= JACCARD_THRESHOLD:
            G.add_edge(b1, b2, weight=jaccard)

print("✅ Graphe terminé !")

# Sauvegarder le graphe avec pickle
with open("jaccard_graph.gpickle", "wb") as f:
    pickle.dump(G, f)

print("💾 Graphe sauvegardé dans jaccard_graph.gpickle")


