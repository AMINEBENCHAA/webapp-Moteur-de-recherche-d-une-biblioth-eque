
> **Projet académique DAAR** (Développement d'Applications et Algorithmes Répartis)  
> Un moteur de recherche full-stack avec indexation avancée, classement intelligent et interface web moderne.

---

## 🎯 Fonctionnalités

### Recherche Avancée
- ✅ **Recherche simple** par mot-clé avec indexation inversée
- ✅ **Recherche RegEx** pour des patterns complexes
- ✅ **Autocomplétion intelligente** en temps réel
- ✅ **Suggestions personnalisées** basées sur le graphe de similarité Jaccard






---

## 🚀 Installation & Déploiement

### Prérequis
- Python 3.11+
- pip
- 10 GB d'espace disque (pour la bibliothèque)

### Phase 1 : Installation Initiale


# 1. Cloner le repository
```bash 
git clone https://github.com/votre-username/webapp-Moteur-de-recherche.git
cd webapp-Moteur-de-recherche
```
# 2. Créer et activer l'environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate     # Windows
```
# 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### Phase 2 : Récupération des Données


# Télécharger les livres depuis Project Gutenberg
#### Cette étape peut prendre 1-2 heures selon votre connexion
python data/retrieveScript.py

#### Résultat attendu : ~1664+ livres dans le dossier books/


## Phase 3 : Traitement des Données


# 1. Construire l'index inversé
```
python createIndex.py
```
### ⏱️ Durée estimée : 10-30 minutes
### 📦 Génère : index.json, books_list.json

# 2. Construire le graphe de Jaccard
```
python jaccard.py
```
### ⏱️ Durée estimée : 30-60 minutes
### 📦 Génère : jaccard_graph.gpickle

# 3. Tester le graphe (optionnel)
python pickletest.py
# ✓ Vérifie l'intégrité du graphe


### Phase 4 : Lancement de l'Application

```bash
# Lancer le backend Flask
python app.py
```
#### 🌐 API accessible sur : http://localhost:5000
#####  📖 Endpoints disponibles :
#####   GET /health
#####  GET /search?query=mot&ranking=hybrid
#####    GET /advanced-search?regex=pattern
#####    GET /suggestions?query=mot
#####    GET /download/<filename>
#####    GET /stats


### Frontend

Ouvrez simplement `frontend/index.html` dans votre navigateur, ou déployez sur :
- **Vercel** 
- **Netlify**
-

---

## 🧪 Tests de Performance

### Installation des outils de test

```bash
cd tests
pip install -r test_requirements.txt
```

### Lancer la suite de tests

```bash
python performance_test.py
```

### Résultats générés

Le script génère automatiquement :

📊 **Graphiques** (dans `performance_tests/`) :
- `response_times_by_category.png` - Distribution par catégorie de mots
- `simple_vs_regex.png` - Comparaison recherche simple vs RegEx
- `ranking_comparison.png` - Performance des algorithmes de classement
- `load_test.png` - Test de charge concurrent (50 requêtes)
- `comprehensive_summary.png` - Tableau de bord complet

📝 **Rapport** :
- `rapport_performance.txt` - Statistiques détaillées avec recommandations

📦 **Données brutes** :
- `test_results_YYYYMMDD_HHMMSS.json` - Export JSON

### Métriques clés

- ⏱️ Temps de réponse (min, max, moyenne, médiane, P95, P99)
- 📈 Débit (requêtes/seconde)
- ✅ Taux de succès
- 📊 Comparaison des algorithmes de classement
- 🔥 Performance sous charge (test concurrent)

---

## 📖 Utilisation de l'API

### Exemples de requêtes

```bash
# Vérifier l'état de l'API
curl http://localhost:5000/health

# Recherche simple
curl "http://localhost:5000/search?query=love&ranking=hybrid"

# Recherche RegEx
curl "http://localhost:5000/advanced-search?regex=^qu.*&ranking=pagerank"

# Obtenir des suggestions
curl "http://localhost:5000/suggestions?query=love&top_n=5"

# Télécharger un livre
curl "http://localhost:5000/download/<livre>" -o livre.txt

# Statistiques globales
curl http://localhost:5000/stats
```



