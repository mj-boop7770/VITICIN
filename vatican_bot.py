import os
import json
import requests

# ==========================================
# 1. CONFIGURATION & RÉCUPÉRATION DES CLÉS
# ==========================================
FOOTBALL_KEY = os.environ.get("FOOTBALL_API_KEY")
NEWS_KEY = os.environ.get("NEWS_API_KEY")
GITHUB_TOKEN = os.environ.get("GH_TOKEN")

print("=== [VATICAN ENGINE] MONDIAL & MERCATO FUTUR ===")

if not FOOTBALL_KEY:
    print("❌ Erreur : FOOTBALL_API_KEY manquante.")
    exit(1)

# Toutes les compétitions sont activées en même temps !
COMPETITIONS = {
    "WC": "Coupe du Monde 2026",
    "PL": "Premier League",
    "SA": "Série A",
    "PD": "La Liga",
    "FL1": "Ligue 1",
    "CL": "Ligue des Champions"
}

headers = {"X-Auth-Token": FOOTBALL_KEY}
donnees_vatican = []

# ==========================================
# 2. CHASSE AUX INFOS (MONDIAL OU MERCATO CLUBS)
# ==========================================
def obtenir_actu_vatican(requete_recherche):
    if not NEWS_KEY:
        return "Signal actualité indisponible."
    
    url_news = f"https://newsapi.org/v2/everything?q={requete_recherche}&language=fr&sortBy=publishedAt&pageSize=3&apiKey={NEWS_KEY}"
    
    try:
        reponse = requests.get(url_news, timeout=10)
        if reponse.status_code == 200:
            articles = reponse.json().get("articles", [])
            if articles:
                titres = [art["title"] for art in articles if art["title"]]
                return " | ".join(titres[:2])
            return "Calme plat dans les coulisses de cette ligue."
        return "Recherche en cours..."
    except Exception:
        return "Impossible de scanner l'actualité."

# ==========================================
# 3. CORE PROCESSOR : MATCHS EN DIRECT + PRÉPARATION DE L'AVENIR
# ==========================================
for comp_code, comp_nom in COMPETITIONS.items():
    print(f"📡 Analyse Vatican -> {comp_nom}...")
    
    url_foot = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"
    
    try:
        res = requests.get(url_foot, headers=headers, timeout=10)
        matchs_transformes = []
        
        if res.status_code == 200:
            matchs_api = res.json().get("matches", [])
            
            # On cherche s'il y a des matchs programmés ou en cours (ex: Coupe du Monde)
            matchs_actifs = [m for m in matchs_api if m.get("status") in ["SCHEDULED", "LIVE", "IN_PLAY", "TIMED"]]
            
            if matchs_actifs:
                for m in matchs_actifs[:4]:
                    home = m["homeTeam"]["name"]
                    away = m["awayTeam"]["name"]
                    
                    score_txt = "VS"
                    if m.get("status") in ["LIVE", "IN_PLAY"]:
                        score_txt = f"{m['score']['fullTime']['home']} - {m['score']['fullTime']['away']}"
                        
                    matchs_transformes.append({
                        "domicile": home,
                        "exterieur": away,
                        "heure": m.get("utcDate", "Heure inconnue"),
                        "score": score_txt,
                        "statut": m.get("status"),
                        "signal_vatican": obtenir_actu_vatican(f'"{home}" OR "{away}"')
                    })
        
        # --- PRÉPARATION DE L'AVENIR (Si la ligue européenne n'a pas encore de matchs fixés) ---
        if not matchs_transformes and comp_code != "WC":
            print(f"   ℹ️ Mode Mercato activé pour {comp_nom}")
            # On va chercher les rumeurs de transfert et changements de cette ligue spécifique
            flash_mercato = obtenir_actu_vatican(f'transfert mercato {comp_nom}')
            
            matchs_transformes.append({
                "domicile": "Mercato & Transferts",
                "exterieur": "Changements Clubs",
                "heure": "Saison 2026/2027 en préparation",
                "score": "🔄",
                "statut": "MERCATO",
                "signal_vatican": f"🔥 Coulisses : {flash_mercato}"
            })
            
        if matchs_transformes:
            donnees_vatican.append({
                "ligue": comp_nom,
                "matchs": matchs_transformes
            })
            
    except Exception as e:
        print(f"❌ Échec sur la compétition {comp_code} : {str(e)}")

# ==========================================
# 4. ENREGISTREMENT ET PUSH
# ==========================================
print("💾 Gravure des données sur ligues.json...")
with open("ligues.json", "w", encoding="utf-8") as f:
    json.dump(donnees_vatican, f, indent=2, ensure_ascii=False)

print("✅ [VATICAN ENGINE] Parfaitement configuré pour le présent et le futur.")
            
