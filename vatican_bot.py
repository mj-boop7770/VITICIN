import os
import json
import requests
from datetime import datetime, timezone

# ==========================================
# CLÉS API
# ==========================================
FOOTBALL_KEY = os.environ.get("FOOTBALL_API_KEY")
NEWS_KEY = os.environ.get("NEWS_API_KEY")
GNEWS_KEY = os.environ.get("GNEWS_KEY")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
WEATHER_KEY = os.environ.get("OPENWEATHER_KEY")

HEADERS_FOOT = {"X-Auth-Token": FOOTBALL_KEY}
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

COMPETITIONS = {
    "WC": "Coupe du Monde 2026",
    "PL": "Premier League",
    "SA": "Série A",
    "PD": "La Liga",
    "FL1": "Ligue 1",
    "CL": "Ligue des Champions"
}

STADES = {
    "WC": "New York",
    "PL": "London",
    "SA": "Rome",
    "PD": "Madrid",
    "FL1": "Paris",
    "CL": "Europe"
}

print("=== VATICIN ENGINE — ORACLE MUJOS ===")

# ==========================================
# 1. MÉTÉO DU STADE
# ==========================================
def get_meteo(ville):
    if not WEATHER_KEY:
        return "Météo indisponible"
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={ville}&appid={WEATHER_KEY}&units=metric&lang=fr",
            timeout=5
        )
        if r.status_code == 200:
            d = r.json()
            temp = round(d["main"]["temp"])
            desc = d["weather"][0]["description"]
            return f"{temp}°C {desc}"
    except:
        pass
    return "Météo indisponible"

# ==========================================
# 2. FORCE ELO
# ==========================================
def get_elo(equipe):
    try:
        nom = equipe.replace(" ", "_")
        r = requests.get(f"http://api.clubelo.com/{nom}", timeout=5)
        if r.status_code == 200:
            lignes = r.text.strip().split("\n")
            if len(lignes) > 1:
                return round(float(lignes[-1].split(",")[4]))
    except:
        pass
    return 1500

# ==========================================
# 3. NEWS PAR ÉQUIPE
# ==========================================
def get_news(query):
    if NEWS_KEY:
        try:
            r = requests.get(
                f"https://newsapi.org/v2/everything?q={query}&language=fr&sortBy=publishedAt&pageSize=2&apiKey={NEWS_KEY}",
                timeout=5
            )
            if r.status_code == 200:
                articles = r.json().get("articles", [])
                if articles:
                    return " | ".join([a["title"] for a in articles[:2] if a["title"]])
        except:
            pass
    if GNEWS_KEY:
        try:
            r = requests.get(
                f"https://gnews.io/api/v4/search?q={query}&lang=fr&max=2&apikey={GNEWS_KEY}",
                timeout=5
            )
            if r.status_code == 200:
                articles = r.json().get("articles", [])
                if articles:
                    return " | ".join([a["title"] for a in articles[:2] if a["title"]])
        except:
            pass
    return "Aucune actualité disponible"

# ==========================================
# 4. FORME DES ÉQUIPES
# ==========================================
def get_forme(team_id):
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5",
            headers=HEADERS_FOOT,
            timeout=5
        )
        if r.status_code == 200:
            matchs = r.json().get("matches", [])
            forme = []
            for m in matchs:
                if m["homeTeam"]["id"] == team_id:
                    gh = m["score"]["fullTime"]["home"]
                    ga = m["score"]["fullTime"]["away"]
                else:
                    gh = m["score"]["fullTime"]["away"]
                    ga = m["score"]["fullTime"]["home"]
                if gh is not None and ga is not None:
                    if gh > ga: forme.append("V")
                    elif gh == ga: forme.append("N")
                    else: forme.append("D")
            return "".join(forme)
    except:
        pass
    return "?????"

# ==========================================
# 5. CALCUL ORACLE
# ==========================================
def calculer_oracle(elo_dom, elo_ext, forme_dom, forme_ext):
    # Score de forme
    points = {"V": 3, "N": 1, "D": 0}
    score_forme_dom = sum(points.get(r, 1) for r in forme_dom) / max(len(forme_dom), 1)
    score_forme_ext = sum(points.get(r, 1) for r in forme_ext) / max(len(forme_ext), 1)

    # Avantage domicile
    elo_dom_adj = elo_dom + 50 + (score_forme_dom * 20)
    elo_ext_adj = elo_ext + (score_forme_ext * 20)

    total = elo_dom_adj + elo_ext_adj
    proba_dom = round((elo_dom_adj / total) * 100)
    proba_ext = round((elo_ext_adj / total) * 100)
    proba_nul = 100 - proba_dom - proba_ext

    # Signal
    ecart = abs(proba_dom - proba_ext)
    if ecart > 25: signal = "FORT"
    elif ecart > 10: signal = "MOYEN"
    else: signal = "RISQUÉ"

    favori = "DOM" if proba_dom > proba_ext else "EXT"

    return {
        "proba_dom": proba_dom,
        "proba_nul": max(proba_nul, 5),
        "proba_ext": proba_ext,
        "signal": signal,
        "favori": favori
    }

# ==========================================
# 6. CLASSEMENT
# ==========================================
def get_classement(comp_code):
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{comp_code}/standings",
            headers=HEADERS_FOOT,
            timeout=5
        )
        if r.status_code == 200:
            standings = r.json().get("standings", [])
            if standings:
                table = standings[0].get("table", [])
                return [
                    {
                        "pos": t["position"],
                        "equipe": t["team"]["shortName"] or t["team"]["name"],
                        "pts": t["points"],
                        "j": t["playedGames"],
                        "g": t["won"],
                        "n": t["draw"],
                        "p": t["lost"],
                        "bp": t["goalsFor"],
                        "bc": t["goalsAgainst"]
                    }
                    for t in table[:10]
                ]
    except:
        pass
    return []

# ==========================================
# 7. BUTEURS
# ==========================================
def get_buteurs(comp_code):
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{comp_code}/scorers?limit=5",
            headers=HEADERS_FOOT,
            timeout=5
        )
        if r.status_code == 200:
            scorers = r.json().get("scorers", [])
            return [
                {
                    "joueur": s["player"]["name"],
                    "equipe": s["team"]["shortName"] or s["team"]["name"],
                    "buts": s["goals"]
                }
                for s in scorers[:5]
            ]
    except:
        pass
    return []

# ==========================================
# 8. CORE — MATCHS + ORACLE
# ==========================================
vaticin_data = {
    "mise_a_jour": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "ligues": []
}

meteo_cache = {}

for comp_code, comp_nom in COMPETITIONS.items():
    print(f"📡 {comp_nom}...")

    ligue_data = {
        "code": comp_code,
        "nom": comp_nom,
        "meteo": "",
        "classement": [],
        "buteurs": [],
        "matchs": []
    }

    # Météo
    ville = STADES.get(comp_code, "Paris")
    if ville not in meteo_cache:
        meteo_cache[ville] = get_meteo(ville)
    ligue_data["meteo"] = meteo_cache[ville]

    # Classement + buteurs
    ligue_data["classement"] = get_classement(comp_code)
    ligue_data["buteurs"] = get_buteurs(comp_code)

    # Matchs
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{comp_code}/matches",
            headers=HEADERS_FOOT,
            timeout=10
        )
        if r.status_code == 200:
            matchs = r.json().get("matches", [])
            matchs_filtres = [
                m for m in matchs
                if m.get("status") in ["LIVE", "IN_PLAY", "TIMED", "SCHEDULED", "FINISHED"]
            ][:8]

            for m in matchs_filtres:
                home = m["homeTeam"]["shortName"] or m["homeTeam"]["name"]
                away = m["awayTeam"]["shortName"] or m["awayTeam"]["name"]
                home_id = m["homeTeam"]["id"]
                away_id = m["awayTeam"]["id"]

                # Forme
                forme_dom = get_forme(home_id)
                forme_ext = get_forme(away_id)

                # ELO
                elo_dom = get_elo(home)
                elo_ext = get_elo(away)

                # Oracle
                oracle = calculer_oracle(elo_dom, elo_ext, forme_dom, forme_ext)

                # News
                news = get_news(f'"{home}" OR "{away}" football')

                # Score
                score_dom = m["score"]["fullTime"]["home"]
                score_ext = m["score"]["fullTime"]["away"]
                score_txt = f"{score_dom}-{score_ext}" if score_dom is not None else "VS"

                ligue_data["matchs"].append({
                    "domicile": home,
                    "exterieur": away,
                    "heure": m.get("utcDate", ""),
                    "score": score_txt,
                    "statut": m.get("status"),
                    "groupe": (m.get("group") or "").replace("GROUP_", ""),
                    "forme_dom": forme_dom,
                    "forme_ext": forme_ext,
                    "elo_dom": elo_dom,
                    "elo_ext": elo_ext,
                    "oracle": oracle,
                    "news": news,
                    "meteo": ligue_data["meteo"]
                })

    except Exception as e:
        print(f"❌ Erreur {comp_code}: {e}")

    vaticin_data["ligues"].append(ligue_data)

# ==========================================
# 9. SAUVEGARDE
# ==========================================
with open("ligues.json", "w", encoding="utf-8") as f:
    json.dump(vaticin_data, f, indent=2, ensure_ascii=False)

print(f"✅ VATICIN ENGINE — ligues.json généré !")
