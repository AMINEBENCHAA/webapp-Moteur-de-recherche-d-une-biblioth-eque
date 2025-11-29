import os
import re
import json
from collections import defaultdict
from unicodedata import normalize

DATA_DIR = "gutenberg_books"

# Stopwords français courants (on ignore ces mots)
STOPWORDS = {
    'le', 'la', 'les', 'de', 'du', 'des', 'et', 'or', 'mais', 'donc',
    'et', 'ou', 'un', 'une', 'des', 'au', 'aux', 'par', 'pour', 'sur',
    'avec', 'sans', 'sous', 'entre', 'dans', 'chez', 'vers', 'depuis',
    'jusqu', 'à', 'a', 'en', 'is', 'it', 'the', 'a', 'an', 'and', 'or',
    'but', 'in', 'on', 'at', 'to', 'for', 'of', 'by', 'from', 'up',
    'about', 'out', 'if', 'as', 'be', 'been', 'being', 'have', 'has',
    'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
}

def normalize_text(text):
    """Normalise le texte : minuscules, accents supprimés"""
    # Convertir en minuscules
    text = text.lower()
    # Supprimer les accents
    text = normalize('NFKD', text)
    text = ''.join(c for c in text if not normalize('NFD', c)[1:])
    return text

def clean_word(word):
    """Nettoie un mot : supprime la ponctuation, valide"""
    # Supprimer la ponctuation
    word = re.sub(r'[^\w]', '', word)
    # Garder seulement les mots > 2 caractères et != stopwords
    if len(word) > 2 and word not in STOPWORDS:
        return word
    return None

def build_index():
    """Construit un index inversé amélioré avec occurrence counts"""
    print("🔍 Construction de l'index amélioré...")
    
    index = defaultdict(lambda: defaultdict(int))  # word -> {filename: count}
    book_list = []
    
    for filename in sorted(os.listdir(DATA_DIR)):
        if filename.endswith(""):
            filepath = os.path.join(DATA_DIR, filename)
            print(f"  📖 Indexation : {filename}")
            
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                normalized = normalize_text(text)
                words = normalized.split()
                
                # Compter les occurrences de chaque mot
                for word in words:
                    cleaned = clean_word(word)
                    if cleaned:
                        index[cleaned][filename] += 1
                
                book_list.append(filename)
    
    # Convertir en format sérialisable JSON
    index_json = {}
    for word, files_dict in index.items():
        index_json[word] = {
            "files": list(files_dict.keys()),
            "occurrences": files_dict  # {filename: count}
        }
    
    # Sauvegarder l'index
    with open("index.json", "w", encoding="utf-8") as f:
        json.dump(index_json, f)
    
    # Sauvegarder la liste des livres
    with open("books_list.json", "w", encoding="utf-8") as f:
        json.dump(book_list, f)
    
    print(f"\n✅ Index amélioré créé !")
    print(f"   📊 Vocabulaire : {len(index)} mots uniques")
    print(f"   📚 Livres indexés : {len(book_list)}")
    print(f"   💾 Fichiers sauvegardés : index.json, books_list.json")

if __name__ == "__main__":
    build_index()