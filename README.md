# webapp-Moteur-de-recherche-d-une-biblioth-eque
Moteur de recherche intelligent pour bibliothèque numérique - Projet académique  du module DAAR (Développement d'Applications et Algorithmes Répartis). 

#phase initial :
# 1. Créer environnement virtuel
python -m venv venv && source venv/bin/activate

# 2. Installer les deps
pip install -r requirements.txt

# 3.retrieve Data
python data/retrieveScript.py
#phase de traitement :
# 1.  Construire l'index
python createIndex.py
# 2. Construire le graphe (si pas fait)
python jaccard.py
# 3 . tester le graphe 
python pickletest.py
# phase applicatif
# 1. Lancer l'API
python app.py

# tests :
cd tests
pip install -r test_requirements.txt
python performance_test.py
