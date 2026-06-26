import os
import json
import requests

# ==========================================
# 1. CONFIGURATION & RÉCUPÉRATION DES CLÉS BRUTES
# ==========================================
FOOTBALL_KEY = os.environ.get("FOOTBALL_API_KEY")
NEWS_KEY = os.environ.get("NEWS_API_KEY")
GITHUB_TOKEN = os.environ.get("GH_TOKEN")

print("=== [VATICAN ENGINE] INITIALISATION EN DIRECT ===")

if not FOOTBALL_KEY:
    print("❌ Erreur critique : FOOTBALL_API_KEY manquante. Arrêt du traitement réel.")
    exit(1)

# Les 5 ligues réelles suivies par le moteur
COMPETITIONS = {
    "CL": "Ligue des Champions",
    "PL": "Premier League",
    "SA": "Série A",
    "PD": "La Liga",
    "FL1": "Ligue 1"
}

# ==========================================
# 2. CHASSE AUX INFOS RÉELLES (NEWSAPI)
# ==========================================
def obtenir_signal_vatican(equipe_home, equipe_away):
    if not NEWS_KEY:
        return "Signal indisponible (Clé NewsAPI absente)."
    
    requete = f"{equipe_home} OR {equipe_away}"
    url_news = f"https://newsapi.org/v2/everything?q={requete}&language=fr&sortBy=publishedAt&pageSize=3&apiKey={NEWS_KEY}"
    
    try:
        reponse = requests.get(url_news, timeout=10)
        if reponse.status_code == 200:
            articles = reponse.json().get("articles", [])
            if articles:
                titres = [art["title"] for art in articles if art["title"]]
                return " | ".join(titres[:2])
            return "Pas d'alertes médias récentes sur ce match."
        return f"Statut NewsAPI anormal : {reponse.status_code}"
    except Exception as e:
        return f"Erreur scan actualité : {str(e)}"

# ==========================================
# 3. EXTRACTION DU CALENDRIER RÉEL
# ==========================================
donnees_vatican = []
headers = {"X-Auth-Token": FOOTBALL_KEY}

for comp_code, comp_nom in COMPETITIONS.items():
    print(f"📡 Connexion API Football -> Récupération de la : {comp_nom}...")
    url_foot = f"https://api.football-data.org/v4/competitions/{comp_code}/matches?status=SCHEDULED"
    
    try:
        res = requests.get(url_foot, headers=headers, timeout=10)
        if res.status_code == 200:
            matchs_api = res.json().get("matches", [])
            matchs_transformes = []
            
            # Capture des 3 prochains vrais matchs de la ligue
            for m in matchs_api[:3]:
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                
                print(f"   ↳ Match réel détecté : {home} vs {away}")
                signal = obtenir_signal_vatican(home, away)
                
                matchs_transformes.append({
                    "domicile": home,
                    "exterieur": away,
                    "heure": m.get("utcDate", "Heure inconnue"),
                    "score": f"{m['score']['fullTime']['home']} - {m['score']['fullTime']['away']}",
                    "statut": m.get("status", "UNKNOWN"),
                    "signal_vatican": signal
                })
            
            if matchs_transformes:
                donnees_vatican.append({
                    "ligue": comp_nom,
                    "matchs": matchs_transformes
                })
        else:
            print(f"⚠️ Erreur serveur API Football ({comp_code}) : Code {res.status_code}")
    except Exception as e:
        print(f"❌ Échec de traitement pour la ligue {comp_code} : {str(e)}")

# ==========================================
# 4. GRAVURE DU FICHIER LIGUES.JSON
# ==========================================
print("💾 Écriture finale sur ligues.json...")
with open("ligues.json", "w", encoding="utf-8") as f:
    json.dump(donnees_vatican, f, indent=2, ensure_ascii=False)

print("✅ [VATICAN ENGINE] Terminé. Données réelles prêtes pour le Push.")
    
