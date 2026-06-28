import os
import json
import requests
from datetime import datetime, timezone, timedelta

# ==========================================
# CLÉS API
# ==========================================
FOOTBALL_KEY = os.environ.get("FOOTBALL_API_KEY")
NEWS_KEY = os.environ.get("NEWS_API_KEY")
GNEWS_KEY = os.environ.get("GNEWS_KEY")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
WEATHER_KEY = os.environ.get("OPENWEATHER_KEY")

HEADERS_FOOT = {"X-Auth-Token": FOOTBALL_KEY}
NOW = datetime.now(timezone.utc)
TODAY = NOW.strftime("%Y-%m-%d")
DANS_7J = (NOW + timedelta(days=7)).strftime("%Y-%m-%d")

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
    "CL": "London"
}

print("=== VATICIN ENGINE — ORACLE MUJOS ===")
print(f"📅 Date : {TODAY}")

# ==========================================
# 1. MÉTÉO
# ==========================================
def get_meteo(ville):
    if not WEATHER_KEY:
        return ""
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
    return ""

# ==========================================
# 2. FORME VIA RAPIDAPI
# ==========================================
def get_forme_rapidapi(team_id):
    if not RAPIDAPI_KEY:
        return "?????"
    try:
        r = requests.get(
            "https://api-football-v1.p.rapidapi.com/v3/fixtures",
            headers={
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            },
            params={"team": team_id, "last": 5},
            timeout=5
        )
        if r.status_code == 200:
            fixtures = r.json().get("response", [])
            forme = []
            for f in fixtures:
                teams = f["teams"]
                goals = f["goals"]
                if teams["home"]["id"] == team_id:
                    gf, ga = goals["home"], goals["away"]
                else:
                    gf, ga = goals["away"], goals["home"]
                if gf is None or ga is None:
                    continue
                if gf > ga: forme.append("V")
                elif gf == ga: forme.append("N")
                else: forme.append("D")
            return "".join(forme) if forme else "?????"
    except:
        pass
    return "?????"

# ==========================================
# 3. NEWS CIBLÉES
# ==========================================
news_cache = {}

def get_news(home, away):
    key = f"{home}_{away}"
    if key in news_cache:
        return news_cache[key]

    queries = [f'"{home}"', f'"{away}"', f"{home} {away}"]
    for query in queries:
        if NEWS_KEY:
            try:
                r = requests.get(
                    f"https://newsapi.org/v2/everything?q={query}&language=fr&sortBy=publishedAt&pageSize=1&apiKey={NEWS_KEY}",
                    timeout=5
                )
                if r.status_code == 200:
                    articles = r.json().get("articles", [])
                    if articles and articles[0].get("title"):
                        result = articles[0]["title"]
                        news_cache[key] = result
                        return result
            except:
                pass
        if GNEWS_KEY:
            try:
                r = requests.get(
                    f"https://gnews.io/api/v4/search?q={query}&lang=fr&max=1&apikey={GNEWS_KEY}",
                    timeout=5
                )
                if r.status_code == 200:
                    articles = r.json().get("articles", [])
                    if articles and articles[0].get("title"):
                        result = articles[0]["title"]
                        news_cache[key] = result
                        return result
            except:
                pass

    news_cache[key] = ""
    return ""

# ==========================================
# 4. ORACLE ELO SIMPLIFIÉ
# ==========================================
def calculer_oracle(forme_dom, forme_ext, statut):
    points = {"V": 3, "N": 1, "D": 0}

    score_dom = sum(points.get(r, 1) for r in forme_dom if r in points)
    score_ext = sum(points.get(r, 1) for r in forme_ext if r in points)

    base_dom = 50 + (score_dom * 3) - (score_ext * 2)
    base_ext = 50 + (score_ext * 3) - (score_dom * 2)

    # Avantage domicile
    base_dom += 8

    total = base_dom + base_ext
    proba_dom = max(10, min(80, round(base_dom / total * 100)))
    proba_ext = max(10, min(80, round(base_ext / total * 100)))
    proba_nul = max(5, 100 - proba_dom - proba_ext)

    ecart = abs(proba_dom - proba_ext)
    if ecart > 20: signal = "FORT"
    elif ecart > 10: signal = "MOYEN"
    else: signal = "RISQUÉ"

    return {
        "proba_dom": proba_dom,
        "proba_nul": proba_nul,
        "proba_ext": proba_ext,
        "signal": signal,
        "favori": "DOM" if proba_dom > proba_ext else "EXT"
    }

# ==========================================
# 5. CLASSEMENT
# ==========================================
def get_classement(comp_code):
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{comp_code}/standings",
            headers=HEADERS_FOOT,
            timeout=8
        )
        if r.status_code == 200:
            standings = r.json().get("standings", [])
            if standings:
                table = standings[0].get("table", [])
                return [{
                    "pos": t["position"],
                    "equipe": t["team"]["shortName"] or t["team"]["name"],
                    "pts": t["points"],
                    "j": t["playedGames"],
                    "g": t["won"],
                    "n": t["draw"],
                    "p": t["lost"],
                    "bp": t["goalsFor"],
                    "bc": t["goalsAgainst"]
                } for t in table[:10]]
    except:
        pass
    return []

# ==========================================
# 6. BUTEURS
# ==========================================
def get_buteurs(comp_code):
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{comp_code}/scorers?limit=5",
            headers=HEADERS_FOOT,
            timeout=8
        )
        if r.status_code == 200:
            scorers = r.json().get("scorers", [])
            return [{
                "joueur": s["player"]["name"],
                "equipe": s["team"]["shortName"] or s["team"]["name"],
                "buts": s["goals"]
            } for s in scorers[:5]]
    except:
        pass
    return []

# ==========================================
# 7. CHARGER HISTORIQUE
# ==========================================
def charger_historique():
    try:
        with open("historique.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"total_matchs": 0, "matchs": []}

def sauvegarder_historique(historique, nouveaux_matchs):
    ids_existants = {m["id"] for m in historique["matchs"]}
    ajoutes = 0
    for m in nouveaux_matchs:
        if m["id"] not in ids_existants and m["statut"] == "FINISHED":
            historique["matchs"].append(m)
            ajoutes += 1
    historique["total_matchs"] = len(historique["matchs"])
    historique["derniere_maj"] = TODAY
    print(f"📚 Historique : {historique['total_matchs']} matchs ({ajoutes} nouveaux)")
    return historique

# ==========================================
# 8. CORE — TRAITEMENT PRINCIPAL
# ==========================================
vaticin_data = {
    "mise_a_jour": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "ligues": []
}

historique = charger_historique()
tous_matchs_historique = []
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

    # Classement + Buteurs
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
            tous_matchs = r.json().get("matches", [])

            # Filtrer : live + 7 prochains jours + 3 derniers terminés
            live = [m for m in tous_matchs if m["status"] in ["LIVE", "IN_PLAY"]]
            a_venir = [m for m in tous_matchs
                      if m["status"] in ["TIMED", "SCHEDULED"]
                      and m["utcDate"][:10] <= DANS_7J][:6]
            termines = [m for m in tous_matchs
                       if m["status"] == "FINISHED"][-3:]

            matchs_selectionnes = live + termines + a_venir

            for m in matchs_selectionnes:
                home = m["homeTeam"]["shortName"] or m["homeTeam"]["name"]
                away = m["awayTeam"]["shortName"] or m["awayTeam"]["name"]
                home_id = m["homeTeam"]["id"]
                away_id = m["awayTeam"]["id"]

                # Forme
                forme_dom = get_forme_rapidapi(home_id)
                forme_ext = get_forme_rapidapi(away_id)

                # Oracle
                oracle = calculer_oracle(forme_dom, forme_ext, m["status"])

                # News ciblées
                news = get_news(home, away)

                # Score
                sh = m["score"]["fullTime"]["home"]
                sa = m["score"]["fullTime"]["away"]
                score_txt = f"{sh}-{sa}" if sh is not None else "VS"

                match_data = {
                    "id": m["id"],
                    "domicile": home,
                    "exterieur": away,
                    "heure": m.get("utcDate", ""),
                    "score": score_txt,
                    "statut": m.get("status"),
                    "groupe": (m.get("group") or "").replace("GROUP_", ""),
                    "forme_dom": forme_dom,
                    "forme_ext": forme_ext,
                    "oracle": oracle,
                    "news": news,
                    "meteo": ligue_data["meteo"],
                    "ligue": comp_nom,
                    "date": m.get("utcDate", "")[:10]
                }

                ligue_data["matchs"].append(match_data)
                tous_matchs_historique.append(match_data)

    except Exception as e:
        print(f"❌ {comp_code}: {e}")

    vaticin_data["ligues"].append(ligue_data)

# ==========================================
# 9. SAUVEGARDE
# ==========================================
# ligues.json — données actuelles
with open("ligues.json", "w", encoding="utf-8") as f:
    json.dump(vaticin_data, f, indent=2, ensure_ascii=False)
print("✅ ligues.json mis à jour")

# historique.json — accumulation
historique = sauvegarder_historique(historique, tous_matchs_historique)
with open("historique.json", "w", encoding="utf-8") as f:
    json.dump(historique, f, indent=2, ensure_ascii=False)
print("✅ historique.json mis à jour")

print("=== VATICIN ENGINE — TERMINÉ ===")
