import os
import requests
import json
import time
from datetime import datetime

CHANNEL = "ABHITAK"
CATEGORIES = ["general", "business", "entertainment", "sports"]
LANGUAGES = ["hi", "en"]

# Vernacular & International High-Volatility Keywords for Breaking Alert Classification
CRITICAL_KEYWORDS = [
    "breaking", "crash", "alert", "deadly", "collapse", "attack", "scam", "arrested", "cabinet", "election",
    "ब्रेकिंग", "धमाका", "घोटाला", "गिरफ्तार", "हादसा", "मौत", "क्रैश", "इस्तीफा", "विस्फोट", "बजट", "चुनाव"
]

GNEWS_API_KEY = os.environ.get("NEWS_API_KEY")

def load_existing_database():
    if os.path.exists("news.json"):
        try:
            with open("news.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if "hi" not in data: data["hi"] = {}
                if "en" not in data: data["en"] = {}
                return data
        except Exception:
            return {"hi": {}, "en": {}}
    return {"hi": {}, "en": {}}

def score_article_priority(title, description):
    combined_text = f"{title or ''} {description or ''}".lower()
    matches = sum(1 for word in CRITICAL_KEYWORDS if word in combined_text)
    return "CRITICAL_ALERT" if matches >= 2 else "STANDARD"

def fetch_gnews_stream(category, lang):
    # Mapping regional localization parameter
    country = "in" if lang == "hi" else "us"
    url = f"https://gnews.io/api/v4/top-headlines?category={category}&lang={lang}&country={country}&apikey={GNEWS_API_KEY}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json().get("articles", [])
        print(f"⚠️ API Warning: Node returned status {response.status_code} for [{lang.upper()} - {category.upper()}]")
        return []
    except Exception as e:
        print(f"❌ Handshake Error for [{lang.upper()} - {category.upper()}]: {e}")
        return []

def main():
    if not GNEWS_API_KEY:
        print("Aborting: Operational NEWS_API_KEY secret token variable missing.")
        return

    db = load_existing_database()
    total_new_ingested = 0

    for lang in LANGUAGES:
        for cat in CATEGORIES:
            # Prevent API throttle blocks using a 2-second execution loop rest period
            print(f"Syncing tracking arrays for Layer: [{lang.upper()}] ➔ Track: [{cat.upper()}]")
            time.sleep(2)
            
            if cat not in db[lang]:
                db[lang][cat] = []
                
            raw_items = fetch_gnews_stream(cat, lang)
            existing_urls = {item["url"] for item in db[lang][cat]}
            
            fresh_records = []
            for item in raw_items:
                url = item.get("url")
                if not url or url in existing_urls:
                    continue
                    
                title = item.get("title")
                desc = item.get("description")
                priority = score_article_priority(title, desc)
                
                fresh_records.append({
                    "title": title,
                    "desc": desc,
                    "image": item.get("image") or "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800",
                    "url": url,
                    "source": item.get("source", {}).get("name", "Abhitak News"),
                    "date": item.get("publishedAt") or datetime.utcnow().isoformat(),
                    "priority": priority
                })
                existing_urls.add(url)
                total_new_ingested += 1

            # Accumulate historical archives seamlessly and sort strictly by chronological order
            combined_pool = fresh_records + db[lang][cat]
            combined_pool.sort(key=lambda x: x["date"], reverse=True)
            
            # Clip at 60 individual entries to generate 240+ total active files across network arrays
            db[lang][cat] = combined_pool[:60]

    db["lastGlobalSync"] = datetime.utcnow().isoformat() + "Z"
    
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
        
    print(f"🚀 Master Ledger Compilation successful. Ingested {total_new_ingested} original news updates.")

if __name__ == "__main__":
    main()
