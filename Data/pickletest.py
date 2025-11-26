import pickle

with open("jaccard_graph.gpickle", "rb") as f:
    G = pickle.load(f)



print("\n" + "="*50)
print("📊 INFORMATIONS SUR VOTRE GRAPHE")
print("="*50)

# 2. Informations de base
print(f"\n🔢 Nombre de livres (nœuds) : {G.number_of_nodes()}")
print(f"🔗 Nombre de connexions (arêtes) : {G.number_of_edges()}")
print(f"📈 Type de graphe : {type(G).__name__}")

# 3. Vérifier si le graphe est orienté ou non
if G.is_directed():
    print("➡️  Graphe orienté (DiGraph)")
else:
    print("↔️  Graphe non-orienté (Graph)")

# 4. Afficher quelques nœuds
print(f"\n📚 Exemples de nœuds (IDs de livres) :")
nodes_sample = list(G.nodes())[:10]
print(nodes_sample)

# 5. Afficher quelques arêtes avec leurs poids
print(f"\n🔗 Exemples d'arêtes (connexions entre livres) :")
edges_sample = list(G.edges(data=True))[:5]
for livre1, livre2, data in edges_sample:
    weight = data.get('weight', 'N/A')
    print(f"  Livre {livre1} ↔ Livre {livre2} | Poids: {weight}")

# 6. Statistiques sur les connexions
degrees = dict(G.degree())
print(f"\n📊 Statistiques des connexions :")
print(f"  Connexions min : {min(degrees.values())}")
print(f"  Connexions max : {max(degrees.values())}")
print(f"  Connexions moyenne : {sum(degrees.values()) / len(degrees):.2f}")

# 7. Top 5 livres les plus connectés
top_connected = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:100]
print(f"\n⭐ Top 5 livres les plus connectés :")
for book_id, nb_connexions in top_connected:
    print(f"  Livre {book_id} : {nb_connexions} connexions")

# 8. Vérifier si le graphe a des poids sur les arêtes
sample_edge = list(G.edges(data=True))[0]
if 'weight' in sample_edge[2]:
    print(f"\n✅ Les arêtes ont des poids (coefficients de Jaccard)")
    weights = [data.get('weight', 0) for _, _, data in G.edges(data=True)]
    print(f"  Poids min : {min(weights):.4f}")
    print(f"  Poids max : {max(weights):.4f}")
    print(f"  Poids moyen : {sum(weights)/len(weights):.4f}")
else:
    print(f"\n⚠️  Les arêtes n'ont pas de poids")

print("\n" + "="*50)