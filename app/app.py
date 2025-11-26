import json
import re
import pickle
import networkx as nx
from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import defaultdict
from unicodedata import normalize

app = Flask(__name__)
CORS(app)

# ============ CHARGER LES DONNÉES ============

print("⏳ Chargement des données...")

# Charger l'index amélioré
with open("index.json", "r", encoding="utf-8") as f:
    INDEX = json.load(f)

# Charger la liste des livres
with open("books_list.json", "r", encoding="utf-8") as f:
    BOOKS_LIST = json.load(f)

# Charger le graphe Jaccard
with open("jaccard_graph.gpickle", "rb") as f:
    GRAPH = pickle.load(f)

# Calculer PageRank une fois au démarrage
print("📊 Calcul de PageRank...")
PAGERANK = nx.pagerank(GRAPH)

print("✅ Données chargées ! API prête.")

# ============ FONCTIONS UTILITAIRES ============

def normalize_text(text):
    """Normalise : minuscules + accents supprimés"""
    text = text.lower()
    text = normalize('NFKD', text)
    text = ''.join(c for c in text if not normalize('NFD', c)[1:])
    return text

def get_book_occurrence_count(filename):
    """Retourne le nombre total d'occurrences du mot clé dans le livre"""
    return 0  # sera set par le contexte

def rank_results(results, query_word, ranking_type="hybrid"):
    """
    Classe les résultats selon :
    - "occurrences" : par nombre d'occurrences du mot
    - "pagerank" : par PageRank du livre dans le graphe
    - "hybrid" : combinaison des deux (défaut)
    """
    ranked = []
    
    for filename in results:
        # Nombre d'occurrences du mot clé dans ce livre
        occurrences = INDEX[query_word]["occurrences"].get(filename, 0)
        
        # PageRank du livre (0 s'il n'est pas dans le graphe)
        pagerank_score = PAGERANK.get(filename, 0)
        
        ranked.append({
            "filename": filename,
            "occurrences": occurrences,
            "pagerank": round(pagerank_score, 6),
            "score": occurrences * (1 + pagerank_score * 10)  # Score hybride
        })
    
    # Trier par score décroissant
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked

# ============ ENDPOINTS ============

@app.route("/health", methods=["GET"])
def health():
    """Vérifier que l'API fonctionne"""
    return jsonify({
        "status": "ok",
        "books_count": len(BOOKS_LIST),
        "vocabulary_size": len(INDEX),
        "graph_nodes": GRAPH.number_of_nodes(),
        "graph_edges": GRAPH.number_of_edges()
    })

@app.route("/search", methods=["GET"])
def search():
    """
    Recherche simple par mot-clé
    Params:
    - query: le mot à chercher
    - ranking: "occurrences" | "pagerank" | "hybrid" (défaut)
    """
    query = request.args.get("query", "").strip()
    ranking_type = request.args.get("ranking", "hybrid")
    
    if not query:
        return jsonify({"error": "Paramètre 'query' vide"}), 400
    
    # Normaliser la requête
    query_normalized = normalize_text(query)
    
    # Chercher dans l'index
    if query_normalized not in INDEX:
        return jsonify({
            "query": query,
            "results": [],
            "count": 0,
            "message": "Aucun résultat"
        })
    
    # Récupérer les fichiers contenant le mot
    files = INDEX[query_normalized]["files"]
    
    # Classer les résultats
    ranked = rank_results(files, query_normalized, ranking_type)
    
    return jsonify({
        "query": query,
        "results": ranked,
        "count": len(ranked),
        "ranking_type": ranking_type
    })

@app.route("/advanced-search", methods=["GET"])
def advanced_search():
    """
    Recherche avancée par expression régulière (RegEx)
    Appliquée sur l'index de mots (pas sur le contenu complet pour perf)
    
    Params:
    - regex: l'expression régulière
    - ranking: "occurrences" | "pagerank" | "hybrid"
    """
    regex_pattern = request.args.get("regex", "").strip()
    ranking_type = request.args.get("ranking", "hybrid")
    
    if not regex_pattern:
        return jsonify({"error": "Paramètre 'regex' vide"}), 400
    
    try:
        # Compiler la regex
        pattern = re.compile(regex_pattern, re.IGNORECASE)
    except re.error as e:
        return jsonify({"error": f"RegEx invalide : {str(e)}"}), 400
    
    # Chercher tous les mots qui matchent la regex
    matching_words = [word for word in INDEX.keys() if pattern.search(word)]
    
    if not matching_words:
        return jsonify({
            "regex": regex_pattern,
            "results": [],
            "count": 0,
            "message": "Aucun mot ne correspond à la regex"
        })
    
    # Agréger les résultats de tous les mots matchants
    all_files = set()
    for word in matching_words:
        all_files.update(INDEX[word]["files"])
    
    # Classer les résultats
    ranked = rank_results(list(all_files), matching_words[0] if matching_words else "", ranking_type)
    
    return jsonify({
        "regex": regex_pattern,
        "matching_words": matching_words[:20],  # Top 20 words
        "results": ranked,
        "count": len(ranked),
        "ranking_type": ranking_type
    })

@app.route("/suggestions", methods=["GET"])
def suggestions():
    """
    Suggestions : retourne les livres similaires aux top résultats
    (basé sur les voisins dans le graphe Jaccard)
    
    Params:
    - query: le mot pour lequel chercher des suggestions
    - top_n: nombre de résultats similaires à retourner (défaut 5)
    """
    query = request.args.get("query", "").strip()
    top_n = int(request.args.get("top_n", 5))
    
    if not query:
        return jsonify({"error": "Paramètre 'query' vide"}), 400
    
    # Normaliser
    query_normalized = normalize_text(query)
    
    if query_normalized not in INDEX:
        return jsonify({
            "query": query,
            "suggestions": [],
            "message": "Mot non trouvé"
        })
    
    # Récupérer les top 3 résultats
    files = INDEX[query_normalized]["files"]
    ranked = rank_results(files, query_normalized, "hybrid")
    top_results = ranked[:3]
    
    # Pour chaque top résultat, trouver ses voisins dans le graphe
    suggestions_set = set()
    for result in top_results:
        filename = result["filename"]
        if filename in GRAPH:
            # Récupérer les voisins (livres connectés)
            neighbors = list(GRAPH.neighbors(filename))
            suggestions_set.update(neighbors)
    
    # Filtrer les livres déjà dans les résultats
    suggestions_set = suggestions_set - {r["filename"] for r in top_results}
    
    # Classer les suggestions par PageRank
    suggestions = [
        {
            "filename": s,
            "pagerank": round(PAGERANK.get(s, 0), 6),
            "similarity_score": round(GRAPH[top_results[0]["filename"]][s].get("weight", 0), 4)
            if s in GRAPH and top_results[0]["filename"] in GRAPH and GRAPH.has_edge(top_results[0]["filename"], s)
            else 0
        }
        for s in suggestions_set
    ]
    
    # Trier par PageRank
    suggestions.sort(key=lambda x: x["pagerank"], reverse=True)
    
    return jsonify({
        "query": query,
        "top_results": top_results[:3],
        "suggestions": suggestions[:top_n],
        "count": len(suggestions)
    })

@app.route("/book/<filename>", methods=["GET"])
def get_book(filename):
    """Retourne les métadonnées d'un livre"""
    if filename not in BOOKS_LIST:
        return jsonify({"error": "Livre non trouvé"}), 404
    
    pagerank_score = PAGERANK.get(filename, 0)
    degree = GRAPH.degree(filename) if filename in GRAPH else 0
    
    return jsonify({
        "filename": filename,
        "pagerank": round(pagerank_score, 6),
        "graph_degree": degree,
        "in_graph": filename in GRAPH
    })

@app.route("/stats", methods=["GET"])
def stats():
    """Retourne les statistiques globales du moteur"""
    return jsonify({
        "total_books": len(BOOKS_LIST),
        "vocabulary_size": len(INDEX),
        "graph_nodes": GRAPH.number_of_nodes(),
        "graph_edges": GRAPH.number_of_edges(),
        "graph_density": round(nx.density(GRAPH), 6),
        "top_pagerank_books": [
            {"filename": k, "pagerank": round(v, 6)}
            for k, v in sorted(PAGERANK.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
    })

# ============ MAIN ============

if __name__ == "__main__":
    print("\n🚀 Démarrage de l'API Flask...")
    print("Accès : http://localhost:5000")
    print("Endpoints disponibles :")
    print("  GET /health → État de l'API")
    print("  GET /search?query=mot → Recherche simple")
    print("  GET /advanced-search?regex=pattern → Recherche RegEx")
    print("  GET /suggestions?query=mot → Suggestions")
    print("  GET /book/<filename> → Info sur un livre")
    print("  GET /stats → Statistiques globales")
    print()
    
    app.run(debug=False, host="0.0.0.0", port=5000)