#!/usr/bin/env python3
"""
Script de création du graphe de Jaccard - VERSION CORRIGÉE
Calcule la similarité entre livres et crée un graphe NetworkX
"""

import os
import json
import re
import pickle
import networkx as nx
from collections import defaultdict
from unicodedata import normalize
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = "gutenberg_books"  # Dossier contenant vos livres .txt
JACCARD_THRESHOLD = 0.1       # Seuil : 10% de mots en commun minimum
MIN_WORD_LENGTH = 3           # Ignorer les mots de moins de 3 lettres
MAX_WORDS_PER_BOOK = 50000    # Limiter pour économiser RAM (optionnel)

OUTPUT_FILE = "jaccard_graph.gpickle"
STATS_FILE = "jaccard_stats.json"

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def normalize_word(word):
    """Normalise un mot : minuscules + retire accents"""
    word = word.lower()
    word = normalize('NFKD', word)
    word = ''.join(c for c in word if not normalize('NFD', c)[1:])
    return word

def tokenize_text(text):
    """
    Tokenise le texte en mots propres
    - Minuscules
    - Retire ponctuation
    - Retire nombres
    - Mots >= MIN_WORD_LENGTH
    """
    # Extraire uniquement les mots (lettres)
    words = re.findall(r'\b[a-zA-ZàáâäãåèéêëìíîïòóôöõøùúûüýÿñçÀ-ÿ]+\b', text)
    
    # Normaliser et filtrer
    normalized = set()
    for word in words:
        word_norm = normalize_word(word)
        if len(word_norm) >= MIN_WORD_LENGTH:
            normalized.add(word_norm)
    
    return normalized

def load_book_words(filepath):
    """Charge et tokenise un livre"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        words = tokenize_text(text)
        
        # Limiter le nombre de mots si nécessaire (pour RAM)
        if MAX_WORDS_PER_BOOK and len(words) > MAX_WORDS_PER_BOOK:
            words = set(list(words)[:MAX_WORDS_PER_BOOK])
        
        return words
    
    except Exception as e:
        print(f"❌ Erreur lecture {filepath}: {e}")
        return set()

def calculate_jaccard(set1, set2):
    """Calcule le coefficient de Jaccard entre deux ensembles"""
    if len(set1) == 0 or len(set2) == 0:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return intersection / union

# ============================================================================
# CRÉATION DU GRAPHE
# ============================================================================

def build_jaccard_graph():
    """Construit le graphe de Jaccard"""
    
    print("="*70)
    print("🚀 CONSTRUCTION DU GRAPHE DE JACCARD")
    print("="*70)
    
    # Vérifier que le dossier existe
    if not os.path.exists(DATA_DIR):
        print(f"❌ ERREUR : Le dossier '{DATA_DIR}' n'existe pas !")
        return None
    
    # Lister les livres
    books = [f for f in os.listdir(DATA_DIR) if f.endswith('')]
    print(f"\n📚 {len(books)} livres trouvés dans '{DATA_DIR}'")
    
    if len(books) == 0:
        print("❌ Aucun fichier .txt trouvé !")
        return None
    
    # Étape 1 : Charger tous les livres
    print("\n" + "="*70)
    print("ÉTAPE 1 : Chargement des livres")
    print("="*70)
    
    start_time = time.time()
    book_words = {}
    
    for idx, book in enumerate(books, 1):
        filepath = os.path.join(DATA_DIR, book)
        words = load_book_words(filepath)
        book_words[book] = words
        
        if idx % 100 == 0:
            print(f"  ✓ {idx}/{len(books)} livres chargés... ({len(words)} mots uniques)")
    
    load_time = time.time() - start_time
    print(f"\n✅ Chargement terminé en {load_time:.2f}s")
    
    # Statistiques
    total_words = sum(len(words) for words in book_words.values())
    avg_words = total_words / len(books)
    print(f"   📊 Moyenne : {avg_words:.0f} mots uniques par livre")
    
    # Étape 2 : Créer le graphe
    print("\n" + "="*70)
    print("ÉTAPE 2 : Création du graphe")
    print("="*70)
    
    G = nx.Graph()
    
    # Ajouter tous les livres comme nœuds
    for book in books:
        G.add_node(book)
    
    print(f"✅ {G.number_of_nodes()} nœuds ajoutés")
    
    # Étape 3 : Calculer les arêtes (Jaccard)
    print("\n" + "="*70)
    print("ÉTAPE 3 : Calcul des similarités Jaccard")
    print(f"Seuil : {JACCARD_THRESHOLD} ({JACCARD_THRESHOLD*100:.1f}%)")
    print("="*70)
    
    start_time = time.time()
    total_comparisons = (len(books) * (len(books) - 1)) // 2
    edges_added = 0
    comparisons_done = 0
    
    print(f"\n⏳ {total_comparisons:,} comparaisons à effectuer...")
    print("(Cela peut prendre plusieurs minutes...)\n")
    
    # Calculer pour chaque paire de livres
    for i in range(len(books)):
        book1 = books[i]
        words1 = book_words[book1]
        
        for j in range(i + 1, len(books)):
            book2 = books[j]
            words2 = book_words[book2]
            
            # Calculer Jaccard
            jaccard = calculate_jaccard(words1, words2)
            
            # Ajouter arête si >= seuil
            if jaccard >= JACCARD_THRESHOLD:
                G.add_edge(book1, book2, weight=jaccard)
                edges_added += 1
            
            comparisons_done += 1
            
            # Afficher progression
            if comparisons_done % 10000 == 0:
                percent = (comparisons_done / total_comparisons) * 100
                elapsed = time.time() - start_time
                eta = (elapsed / comparisons_done) * (total_comparisons - comparisons_done)
                print(f"  ✓ {comparisons_done:,}/{total_comparisons:,} ({percent:.1f}%) | "
                      f"Arêtes: {edges_added:,} | ETA: {eta/60:.1f}min")
    
    calc_time = time.time() - start_time
    
    print("\n" + "="*70)
    print("✅ CALCUL TERMINÉ !")
    print("="*70)
    print(f"⏱️  Temps total : {calc_time/60:.2f} minutes")
    print(f"🔗 Arêtes créées : {edges_added:,}")
    print(f"📊 Densité du graphe : {nx.density(G):.6f}")
    
    # Statistiques du graphe
    degrees = dict(G.degree())
    if degrees:
        avg_degree = sum(degrees.values()) / len(degrees)
        max_degree = max(degrees.values())
        min_degree = min(degrees.values())
        
        print(f"\n📈 Statistiques des connexions :")
        print(f"   Moyenne : {avg_degree:.2f} connexions/livre")
        print(f"   Maximum : {max_degree} connexions")
        print(f"   Minimum : {min_degree} connexions")
        
        # Livres les plus connectés
        top_connected = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n⭐ Top 5 livres les plus connectés :")
        for book, degree in top_connected:
            print(f"   {book[:50]}: {degree} connexions")
    
    # Sauvegarder le graphe
    print("\n" + "="*70)
    print("SAUVEGARDE")
    print("="*70)
    
    with open(OUTPUT_FILE, 'wb') as f:
        pickle.dump(G, f)
    
    file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"✅ Graphe sauvegardé : {OUTPUT_FILE} ({file_size:.2f} MB)")
    
    # Sauvegarder les statistiques
    stats = {
        "total_books": len(books),
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "density": nx.density(G),
        "jaccard_threshold": JACCARD_THRESHOLD,
        "avg_degree": avg_degree if degrees else 0,
        "max_degree": max_degree if degrees else 0,
        "min_degree": min_degree if degrees else 0,
        "computation_time_seconds": calc_time,
        "top_connected": [
            {"book": book, "connections": degree}
            for book, degree in top_connected[:10]
        ] if degrees else []
    }
    
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"📊 Statistiques sauvegardées : {STATS_FILE}")
    
    print("\n" + "="*70)
    print("🎉 TERMINÉ !")
    print("="*70)
    
    return G

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """Point d'entrée principal"""
    
    # Vérifier si le graphe existe déjà
    if os.path.exists(OUTPUT_FILE):
        print(f"\n⚠️  Le fichier '{OUTPUT_FILE}' existe déjà !")
        response = input("Voulez-vous le recalculer ? (o/n) : ").strip().lower()
        
        if response != 'o':
            print("❌ Annulé.")
            return
    
    # Construire le graphe
    G = build_jaccard_graph()
    
    if G is not None:
        print(f"\n✅ Succès ! Le graphe est prêt à être utilisé.")
        print(f"📁 Fichier : {OUTPUT_FILE}")
        print(f"\n💡 Vous pouvez maintenant lancer votre API Flask !")

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    main()