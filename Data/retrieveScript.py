import os
import requests
import time

TARGET_BOOKS = 1664
SAVE_DIR = "gutenberg_books"
MIN_WORDS = 10000

os.makedirs(SAVE_DIR, exist_ok=True)

def download_book(book_id):
    """
    Télécharge UNIQUEMENT :
    https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt
    """
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"

    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200 and len(r.text) > 1000:
            return r.text
    except:
        pass

    return None


count_valid = 0
book_id = 180

print("🚀 Début du téléchargement...")

while count_valid < TARGET_BOOKS:
    text = download_book(book_id)

    if text:
        word_count = len(text.split())
        if word_count >= MIN_WORDS:
            filename = os.path.join(SAVE_DIR, f"book_{book_id}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)

            count_valid += 1
            print(f"📚 Livre {book_id} validé ({word_count} mots) — total : {count_valid}")

    time.sleep(0.4)  # éviter de spam le serveur
    book_id += 1

print(f"\n🎉 Téléchargement terminé : {count_valid} livres valides.")
