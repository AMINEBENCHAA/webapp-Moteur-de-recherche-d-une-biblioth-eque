# webapp-Moteur-de-recherche-d-une-biblioth-eque
Moteur de recherche intelligent pour bibliothèque numérique - Projet académique  du module DAAR (Développement d'Applications et Algorithmes Répartis). 


# 1. Créer environnement virtuel
python -m venv venv && source venv/bin/activate

# 2. Installer les deps
pip install -r requirements.txt

# 3. Construire le graphe (si pas fait)
python jaccard.py

# 4. Construire l'index
python createIndex_improved.py

# 5. Lancer l'API
python app.py