"""
Script de test de performance pour le moteur de recherche
Génère des métriques et des graphiques pour analyser les performances
"""

import requests
import time
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Configuration
API_URL = "http://localhost:5000"  # Changez selon votre configuration
OUTPUT_DIR = "performance_tests"
RESULTS_FILE = f"{OUTPUT_DIR}/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# Créer le dossier de sortie
import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Style des graphiques
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# ============ DONNÉES DE TEST ============

# Mots-clés à tester (variété de fréquences)
TEST_QUERIES = {
    "common": ["the", "and", "of", "to", "in"],  # Mots très fréquents
    "medium": ["love", "time", "life", "death", "world"],  # Fréquence moyenne
    "rare": ["quantum", "ephemeral", "serendipity", "labyrinth", "zenith"],  # Mots rares
    "complex": ["^[a-z]{5}$", ".*ing$", "^qu.*", "[aeiou]{3}", "^[^aeiou]+$"]  # RegEx complexes
}

# ============ FONCTIONS DE TEST ============

def test_endpoint_availability():
    """Vérifie que l'API est accessible"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API accessible")
            print(f"   - Livres: {data.get('books_count', 'N/A')}")
            print(f"   - Vocabulaire: {data.get('vocabulary_size', 'N/A')}")
            print(f"   - Nœuds graphe: {data.get('graph_nodes', 'N/A')}")
            return True
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def measure_response_time(endpoint, params=None):
    """Mesure le temps de réponse d'un endpoint"""
    start = time.time()
    try:
        response = requests.get(f"{API_URL}/{endpoint}", params=params, timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "time": elapsed,
                "results_count": data.get("count", 0),
                "status_code": 200
            }
        else:
            return {
                "success": False,
                "time": elapsed,
                "error": f"HTTP {response.status_code}",
                "status_code": response.status_code
            }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "success": False,
            "time": elapsed,
            "error": str(e),
            "status_code": None
        }

def test_search_performance(queries, ranking_type="hybrid"):
    """Test de performance pour la recherche simple"""
    results = []
    
    print(f"\n🔍 Test de recherche simple ({ranking_type})...")
    for category, words in queries.items():
        if category == "complex":  # Skip regex for simple search
            continue
            
        print(f"  Catégorie: {category}")
        for word in words:
            result = measure_response_time("search", {"query": word, "ranking": ranking_type})
            result["query"] = word
            result["category"] = category
            result["type"] = "simple"
            result["ranking"] = ranking_type
            results.append(result)
            
            status = "✓" if result["success"] else "✗"
            print(f"    {status} '{word}': {result['time']:.3f}s")
    
    return results

def test_advanced_search_performance(queries, ranking_type="hybrid"):
    """Test de performance pour la recherche avancée (RegEx)"""
    results = []
    
    print(f"\n🔎 Test de recherche avancée RegEx ({ranking_type})...")
    for category, patterns in queries.items():
        if category != "complex":  # Only test complex patterns
            continue
            
        print(f"  Catégorie: {category}")
        for pattern in patterns:
            result = measure_response_time("advanced-search", {"regex": pattern, "ranking": ranking_type})
            result["query"] = pattern
            result["category"] = category
            result["type"] = "regex"
            result["ranking"] = ranking_type
            results.append(result)
            
            status = "✓" if result["success"] else "✗"
            print(f"    {status} '{pattern}': {result['time']:.3f}s")
    
    return results

def test_suggestions_performance(queries):
    """Test de performance pour les suggestions"""
    results = []
    
    print(f"\n✨ Test de suggestions...")
    test_words = queries["medium"][:3]  # Prendre 3 mots moyens
    
    for word in test_words:
        result = measure_response_time("suggestions", {"query": word, "top_n": 10})
        result["query"] = word
        result["type"] = "suggestions"
        result["category"] = "suggestions"  # Ajout d'une catégorie
        results.append(result)
        
        status = "✓" if result["success"] else "✗"
        print(f"    {status} '{word}': {result['time']:.3f}s")
    
    return results

def test_concurrent_requests(num_requests=50, num_workers=10):
    """Test de charge avec requêtes concurrentes"""
    print(f"\n⚡ Test de charge: {num_requests} requêtes avec {num_workers} workers...")
    
    queries = ["love", "time", "death", "world", "life"] * (num_requests // 5)
    results = []
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for query in queries[:num_requests]:
            future = executor.submit(measure_response_time, "search", {"query": query})
            futures.append(future)
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            if i % 10 == 0:
                print(f"  Complété: {i}/{num_requests}")
    
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r["success"])
    
    print(f"\n  📊 Résultats:")
    print(f"    - Temps total: {total_time:.2f}s")
    print(f"    - Requêtes réussies: {successful}/{num_requests}")
    print(f"    - Débit: {num_requests/total_time:.2f} req/s")
    
    return {
        "results": results,
        "total_time": total_time,
        "throughput": num_requests / total_time,
        "success_rate": successful / num_requests * 100
    }

def test_ranking_comparison():
    """Compare les performances des différents types de classement"""
    print(f"\n📊 Test de comparaison des classements...")
    
    test_word = "love"
    ranking_types = ["hybrid", "occurrences", "pagerank"]
    results = []
    
    for ranking in ranking_types:
        result = measure_response_time("search", {"query": test_word, "ranking": ranking})
        result["ranking"] = ranking
        results.append(result)
        print(f"  {ranking}: {result['time']:.3f}s")
    
    return results

# ============ GÉNÉRATION DE GRAPHIQUES ============

def plot_response_times_by_category(results, output_file):
    """Graphique des temps de réponse par catégorie"""
    df = pd.DataFrame(results)
    df_success = df[df['success'] == True]
    
    if df_success.empty:
        print("⚠️  Pas de résultats réussis pour ce graphique")
        return
    
    plt.figure(figsize=(12, 6))
    
    # Box plot par catégorie
    categories = df_success['category'].unique()
    data_to_plot = [df_success[df_success['category'] == cat]['time'].values for cat in categories]
    
    plt.boxplot(data_to_plot, labels=categories)
    plt.ylabel('Temps de réponse (secondes)')
    plt.xlabel('Catégorie de requête')
    plt.title('Distribution des temps de réponse par catégorie')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Graphique sauvegardé: {output_file}")

def plot_response_times_comparison(results, output_file):
    """Graphique de comparaison simple vs RegEx"""
    df = pd.DataFrame(results)
    df_success = df[df['success'] == True]
    
    if df_success.empty:
        print("⚠️  Pas de résultats réussis pour ce graphique")
        return
    
    plt.figure(figsize=(10, 6))
    
    # Séparer par type
    simple = df_success[df_success['type'] == 'simple']['time']
    regex = df_success[df_success['type'] == 'regex']['time']
    
    data = [simple, regex]
    labels = [f'Simple\n(n={len(simple)})', f'RegEx\n(n={len(regex)})']
    
    bp = plt.boxplot(data, labels=labels, patch_artist=True)
    
    # Couleurs
    colors = ['lightblue', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    plt.ylabel('Temps de réponse (secondes)')
    plt.title('Comparaison des performances: Recherche Simple vs RegEx')
    plt.grid(True, alpha=0.3, axis='y')
    
    # Statistiques
    if len(simple) > 0:
        plt.text(1, max(simple), f'μ={simple.mean():.3f}s', ha='center', va='bottom')
    if len(regex) > 0:
        plt.text(2, max(regex), f'μ={regex.mean():.3f}s', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Graphique sauvegardé: {output_file}")

def plot_ranking_comparison(results, output_file):
    """Graphique de comparaison des méthodes de classement"""
    df = pd.DataFrame(results)
    
    plt.figure(figsize=(10, 6))
    
    rankings = df['ranking'].values
    times = df['time'].values
    
    bars = plt.bar(rankings, times, color=['#3b82f6', '#10b981', '#f59e0b'])
    
    # Ajouter les valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}s', ha='center', va='bottom')
    
    plt.ylabel('Temps de réponse (secondes)')
    plt.xlabel('Méthode de classement')
    plt.title('Performance des différentes méthodes de classement')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Graphique sauvegardé: {output_file}")

def plot_load_test_results(concurrent_results, output_file):
    """Graphique des résultats du test de charge"""
    results = concurrent_results['results']
    df = pd.DataFrame(results)
    df_success = df[df['success'] == True]
    
    if df_success.empty:
        print("⚠️  Pas de résultats réussis pour ce graphique")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Distribution des temps de réponse
    axes[0, 0].hist(df_success['time'], bins=30, color='skyblue', edgecolor='black')
    axes[0, 0].set_xlabel('Temps de réponse (secondes)')
    axes[0, 0].set_ylabel('Fréquence')
    axes[0, 0].set_title('Distribution des temps de réponse')
    axes[0, 0].axvline(df_success['time'].mean(), color='red', linestyle='--', 
                       label=f'Moyenne: {df_success["time"].mean():.3f}s')
    axes[0, 0].legend()
    
    # 2. Temps de réponse au fil du temps
    axes[0, 1].plot(df_success['time'].values, marker='o', markersize=3, linewidth=1)
    axes[0, 1].set_xlabel('Numéro de requête')
    axes[0, 1].set_ylabel('Temps de réponse (secondes)')
    axes[0, 1].set_title('Temps de réponse séquentiel')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Statistiques récapitulatives
    stats_text = f"""
    Statistiques globales:
    
    Requêtes totales: {len(results)}
    Requêtes réussies: {len(df_success)}
    Taux de succès: {concurrent_results['success_rate']:.1f}%
    
    Temps de réponse:
    - Minimum: {df_success['time'].min():.3f}s
    - Maximum: {df_success['time'].max():.3f}s
    - Moyenne: {df_success['time'].mean():.3f}s
    - Médiane: {df_success['time'].median():.3f}s
    - Écart-type: {df_success['time'].std():.3f}s
    
    Débit: {concurrent_results['throughput']:.2f} req/s
    """
    axes[1, 0].text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
                    verticalalignment='center')
    axes[1, 0].axis('off')
    
    # 4. Percentiles
    percentiles = [50, 75, 90, 95, 99]
    values = [np.percentile(df_success['time'], p) for p in percentiles]
    
    axes[1, 1].barh(percentiles, values, color='coral')
    axes[1, 1].set_xlabel('Temps de réponse (secondes)')
    axes[1, 1].set_ylabel('Percentile')
    axes[1, 1].set_title('Temps de réponse par percentile')
    
    for i, (p, v) in enumerate(zip(percentiles, values)):
        axes[1, 1].text(v, i, f' {v:.3f}s', va='center')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Graphique sauvegardé: {output_file}")

def plot_comprehensive_summary(all_results, output_file):
    """Graphique récapitulatif complet"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Résumé complet des tests de performance', fontsize=16, fontweight='bold')
    
    df = pd.DataFrame(all_results)
    df_success = df[df['success'] == True]
    
    if df_success.empty:
        print("⚠️  Pas de résultats réussis pour ce graphique")
        return
    
    # 1. Temps moyen par type de recherche
    type_stats = df_success.groupby('type')['time'].agg(['mean', 'std']).reset_index()
    axes[0, 0].bar(type_stats['type'], type_stats['mean'], 
                   yerr=type_stats['std'], capsize=5, color='steelblue', alpha=0.7)
    axes[0, 0].set_ylabel('Temps moyen (secondes)')
    axes[0, 0].set_title('Performance moyenne par type de recherche')
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    
    # 2. Violin plot par catégorie (filtrer les catégories vides)
    categories = df_success['category'].unique()
    data_violin = []
    valid_categories = []
    for cat in categories:
        cat_data = df_success[df_success['category'] == cat]['time'].values
        if len(cat_data) > 0:  # Seulement si non vide
            data_violin.append(cat_data)
            valid_categories.append(cat)
    
    if len(data_violin) > 0:
        parts = axes[0, 1].violinplot(data_violin, positions=range(len(valid_categories)), 
                                       showmeans=True, showmedians=True)
        axes[0, 1].set_xticks(range(len(valid_categories)))
        axes[0, 1].set_xticklabels(valid_categories)
        axes[0, 1].set_ylabel('Temps de réponse (secondes)')
        axes[0, 1].set_title('Distribution par catégorie (Violin plot)')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
    else:
        axes[0, 1].text(0.5, 0.5, 'Données insuffisantes', ha='center', va='center')
        axes[0, 1].set_title('Distribution par catégorie')
    
    # 3. Taux de succès
    success_counts = df['success'].value_counts()
    success_rate = success_counts.get(True, 0)
    failure_rate = success_counts.get(False, 0)
    
    if success_rate + failure_rate > 0:
        colors_pie = ['#10b981', '#ef4444']
        axes[1, 0].pie([success_rate, failure_rate], 
                       labels=['Succès', 'Échec'], autopct='%1.1f%%',
                       colors=colors_pie, startangle=90)
        axes[1, 0].set_title(f'Taux de succès global\n({len(df)} requêtes)')
    else:
        axes[1, 0].text(0.5, 0.5, 'Pas de données', ha='center', va='center')
        axes[1, 0].set_title('Taux de succès')
    
    # 4. Heatmap des temps par catégorie et type
    try:
        pivot = df_success.pivot_table(values='time', index='category', 
                                        columns='type', aggfunc='mean')
        if not pivot.empty and pivot.shape[0] > 0 and pivot.shape[1] > 0:
            sns.heatmap(pivot, annot=True, fmt='.3f', cmap='YlOrRd', 
                       ax=axes[1, 1], cbar_kws={'label': 'Temps (s)'})
            axes[1, 1].set_title('Temps moyen (catégorie × type)')
        else:
            axes[1, 1].text(0.5, 0.5, 'Données insuffisantes\npour la heatmap', 
                           ha='center', va='center')
            axes[1, 1].set_title('Temps moyen (catégorie × type)')
    except Exception as e:
        axes[1, 1].text(0.5, 0.5, f'Erreur heatmap:\n{str(e)[:50]}', 
                       ha='center', va='center', fontsize=8)
        axes[1, 1].set_title('Temps moyen (catégorie × type)')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Graphique sauvegardé: {output_file}")

# ============ GÉNÉRATION DE RAPPORT ============

def generate_report(all_results, concurrent_results, output_file):
    """Génère un rapport textuel détaillé"""
    df = pd.DataFrame(all_results)
    df_success = df[df['success'] == True]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RAPPORT DE TEST DE PERFORMANCE - MOTEUR DE RECHERCHE\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"API URL: {API_URL}\n\n")
        
        # Statistiques globales
        f.write("1. STATISTIQUES GLOBALES\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total de requêtes testées: {len(df)}\n")
        f.write(f"Requêtes réussies: {len(df_success)} ({len(df_success)/len(df)*100:.1f}%)\n")
        f.write(f"Requêtes échouées: {len(df) - len(df_success)} ({(len(df) - len(df_success))/len(df)*100:.1f}%)\n\n")
        
        if not df_success.empty:
            # Temps de réponse
            f.write("2. TEMPS DE RÉPONSE\n")
            f.write("-" * 80 + "\n")
            f.write(f"Minimum: {df_success['time'].min():.3f}s\n")
            f.write(f"Maximum: {df_success['time'].max():.3f}s\n")
            f.write(f"Moyenne: {df_success['time'].mean():.3f}s\n")
            f.write(f"Médiane: {df_success['time'].median():.3f}s\n")
            f.write(f"Écart-type: {df_success['time'].std():.3f}s\n\n")
            
            # Percentiles
            f.write("Percentiles:\n")
            for p in [50, 75, 90, 95, 99]:
                f.write(f"  P{p}: {np.percentile(df_success['time'], p):.3f}s\n")
            f.write("\n")
            
            # Par type de recherche
            f.write("3. PERFORMANCE PAR TYPE DE RECHERCHE\n")
            f.write("-" * 80 + "\n")
            for search_type in df_success['type'].unique():
                subset = df_success[df_success['type'] == search_type]
                f.write(f"\n{search_type.upper()}:\n")
                f.write(f"  Nombre de requêtes: {len(subset)}\n")
                f.write(f"  Temps moyen: {subset['time'].mean():.3f}s\n")
                f.write(f"  Temps min: {subset['time'].min():.3f}s\n")
                f.write(f"  Temps max: {subset['time'].max():.3f}s\n")
                f.write(f"  Écart-type: {subset['time'].std():.3f}s\n")
            f.write("\n")
            
            # Par catégorie
            f.write("4. PERFORMANCE PAR CATÉGORIE\n")
            f.write("-" * 80 + "\n")
            for category in df_success['category'].unique():
                # Vérifier que la catégorie n'est pas NaN ou None
                if pd.isna(category):
                    continue
                subset = df_success[df_success['category'] == category]
                if len(subset) > 0:
                    f.write(f"\n{str(category).upper()}:\n")
                    f.write(f"  Nombre de requêtes: {len(subset)}\n")
                    f.write(f"  Temps moyen: {subset['time'].mean():.3f}s\n")
                    f.write(f"  Temps min: {subset['time'].min():.3f}s\n")
                    f.write(f"  Temps max: {subset['time'].max():.3f}s\n")
            f.write("\n")
        
        # Test de charge
        if concurrent_results:
            f.write("5. TEST DE CHARGE CONCURRENT\n")
            f.write("-" * 80 + "\n")
            f.write(f"Temps total: {concurrent_results['total_time']:.2f}s\n")
            f.write(f"Débit: {concurrent_results['throughput']:.2f} requêtes/seconde\n")
            f.write(f"Taux de succès: {concurrent_results['success_rate']:.1f}%\n\n")
        
        # Recommandations
        f.write("6. RECOMMANDATIONS\n")
        f.write("-" * 80 + "\n")
        if not df_success.empty:
            avg_time = df_success['time'].mean()
            if avg_time < 0.1:
                f.write("✓ Excellent: Temps de réponse moyen < 100ms\n")
            elif avg_time < 0.5:
                f.write("✓ Bon: Temps de réponse moyen < 500ms\n")
            elif avg_time < 1.0:
                f.write("⚠ Acceptable: Temps de réponse moyen < 1s\n")
                f.write("  Considérez l'optimisation des requêtes les plus lentes\n")
            else:
                f.write("✗ À améliorer: Temps de réponse moyen > 1s\n")
                f.write("  Recommandations:\n")
                f.write("  - Optimiser les algorithmes de recherche\n")
                f.write("  - Ajouter du cache pour les requêtes fréquentes\n")
                f.write("  - Indexer les données différemment\n")
        
        f.write("\n" + "=" * 80 + "\n")
    
    print(f"  ✓ Rapport sauvegardé: {output_file}")

# ============ MAIN ============

def main():
    print("=" * 80)
    print("TEST DE PERFORMANCE - MOTEUR DE RECHERCHE")
    print("=" * 80)
    
    # Vérifier la disponibilité de l'API
    if not test_endpoint_availability():
        print("\n❌ L'API n'est pas accessible. Assurez-vous que le backend est lancé.")
        return
    
    print("\n" + "=" * 80)
    print("DÉBUT DES TESTS")
    print("=" * 80)
    
    all_results = []
    
    # Test 1: Recherche simple
    results_simple = test_search_performance(TEST_QUERIES, "hybrid")
    all_results.extend(results_simple)
    
    # Test 2: Recherche avancée
    results_regex = test_advanced_search_performance(TEST_QUERIES, "hybrid")
    all_results.extend(results_regex)
    
    # Test 3: Suggestions
    results_suggestions = test_suggestions_performance(TEST_QUERIES)
    all_results.extend(results_suggestions)
    
    # Test 4: Comparaison des classements
    results_ranking = test_ranking_comparison()
    
    # Test 5: Test de charge
    concurrent_results = test_concurrent_requests(num_requests=50, num_workers=10)
    
    # Sauvegarder les résultats bruts
    print("\n💾 Sauvegarde des résultats...")
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "all_results": all_results,
            "ranking_comparison": results_ranking,
            "concurrent_test": {
                "total_time": concurrent_results["total_time"],
                "throughput": concurrent_results["throughput"],
                "success_rate": concurrent_results["success_rate"]
            }
        }, f, indent=2)
    print(f"  ✓ Résultats sauvegardés: {RESULTS_FILE}")
    
    # Générer les graphiques
    print("\n📊 Génération des graphiques...")
    plot_response_times_by_category(all_results, f"{OUTPUT_DIR}/response_times_by_category.png")
    plot_response_times_comparison(all_results, f"{OUTPUT_DIR}/simple_vs_regex.png")
    plot_ranking_comparison(results_ranking, f"{OUTPUT_DIR}/ranking_comparison.png")
    plot_load_test_results(concurrent_results, f"{OUTPUT_DIR}/load_test.png")
    plot_comprehensive_summary(all_results, f"{OUTPUT_DIR}/comprehensive_summary.png")
    
    # Générer le rapport
    print("\n📝 Génération du rapport...")
    generate_report(all_results, concurrent_results, f"{OUTPUT_DIR}/rapport_performance.txt")
    
    print("\n" + "=" * 80)
    print("✅ TESTS TERMINÉS")
    print("=" * 80)
    print(f"\nRésultats disponibles dans: {OUTPUT_DIR}/")
    print("  - Graphiques: *.png")
    print("  - Données brutes: *.json")
    print("  - Rapport textuel: rapport_performance.txt")

if __name__ == "__main__":
    main()