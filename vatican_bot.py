import os
import json
import requests
from datetime import datetime, timezone, timedelta

FOOTBALL_KEY = os.environ.get("FOOTBALL_API_KEY")
NEWS_KEY = os.environ.get("NEWS_API_KEY")
GNEWS_KEY = os.environ.get("GNEWS_KEY")
WEATHER_KEY = os.environ.get("OPENWEATHER_KEY")

HEADERS = {"X-Auth-Token": FOOTBALL_KEY}
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

DEBUT_SAISON = {
    "PL": "2026-08-21",
    "SA": "2026-08-23",
    "PD": "2026-08-28",
    "FL1": "2026-08-22",
    "CL": "2026-09-15"
}

print("=== VATICIN ENGINE — ORACLE MUJOS ===")
print(f"📅 Date : {TODAY}")

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
            icons = {"clear sky":"☀️","few clouds":"🌤️","scattered clouds":"⛅","broken clouds":"🌥️","shower rain":"🌦️","rain":"🌧️","thunderstorm":"⛈️","snow":"❄️","mist":"🌫️","overcast clouds":"☁️"}
            icon = next((v for k,v in icons.items() if k in desc.lower()), "🌡️")
            return f"{icon} {temp}°C {desc}"
    except:
        pass
    return ""

def get_forme(team_id):
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5",
            headers=HEADERS,
            timeout=8
        )
        if r.status_code == 200:
            matchs = r.json().get("matches", [])
            forme = []
            buts_pour = 0
            buts_contre = 0
            for m in matchs:
                if m["homeTeam"]["id"] == team_id:
                    gf = m["score"]["fullTime"]["home"]
                    ga = m["score"]["fullTime"]["away"]
                else:
                    gf = m["score"]["fullTime"]["away"]
                    ga = m["score"]["fullTime"]["home"]
                if gf is None or ga is None:
                    continue
                buts_pour += gf
                buts_contre += ga
                if gf > ga: forme.append("V")
                elif gf == ga: forme.append("N")
                else: forme.append("D")
            return {
                "forme": "".join(forme) if forme else "",
                "buts_pour": buts_pour,
                "buts_contre": buts_contre,
                "matchs": len(forme)
            }
    except:
        pass
    return {"forme": "", "buts_pour": 0, "buts_contre": 0, "matchs": 0}

def calculer_oracle(stats_dom, stats_ext, pos_dom=None, pos_ext=None, total_equipes=20):
    points = {"V": 3, "N": 1, "D": 0}
    forme_dom = stats_dom.get("forme", "")
    forme_ext = stats_ext.get("forme", "")
    score_forme_dom = sum(points.get(r, 1) for r in forme_dom if r in points)
    score_forme_ext = sum(points.get(r, 1) for r in forme_ext if r in points)
    att_dom = stats_dom.get("buts_pour", 0) * 2 - stats_dom.get("buts_contre", 0)
    att_ext = stats_ext.get("buts_pour", 0) * 2 - stats_ext.get("buts_contre", 0)
    rang_dom = (total_equipes - (pos_dom or total_equipes//2)) * 3 if pos_dom else 0
    rang_ext = (total_equipes - (pos_ext or total_equipes//2)) * 3 if pos_ext else 0
    score_dom = 50 + (score_forme_dom * 3) + att_dom + rang_dom + 8
    score_ext = 50 + (score_forme_ext * 3) + att_ext + rang_ext
    total = max(score_dom + score_ext, 1)
    proba_dom = max(15, min(80, round(score_dom / total * 100)))
    proba_ext = max(15, min(80, round(score_ext / total * 100)))
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

def generer_analyse(home, away, oracle, stats_dom, stats_ext, statut, score, groupe=""):
    lignes = []
    if groupe:
        lignes.append(f"⚽ Groupe {groupe}")
    if oracle["signal"] != "RISQUÉ":
        fav = home if oracle["favori"] == "DOM" else away
        pct = oracle["proba_dom"] if oracle["favori"] == "DOM" else oracle["proba_ext"]
        lignes.append(f"🎯 Favori : {fav} ({pct}%)")
    else:
        lignes.append(f"⚖️ Match serré")
    if stats_dom.get("forme") and stats_dom["forme"] not in ["?????",""]:
        lignes.append(f"📈 {home} : {stats_dom['forme']} | {stats_dom['buts_pour']} buts")
    if stats_ext.get("forme") and stats_ext["forme"] not in ["?????",""]:
        lignes.append(f"📉 {away} : {stats_ext['forme']} | {stats_ext['buts_pour']} buts")
    if statut == "FINISHED" and score != "VS":
        lignes.append(f"✅ {score}")
    return " • ".join(lignes) if lignes else ""

def get_news_globales():
    print("📰 Récupération des news foot...")
    articles = []
    mots_foot = ["football","foot","soccer","match","but","goal","transfert","mercato",
                 "ligue","champion","coupe","mondial","fifa","uefa","messi","ronaldo",
                 "mbappé","haaland","neymar","kane","salah","club","stade","ballon"]

    if GNEWS_KEY:
        queries = ["football 2026", "mercato transfert club 2026", "coupe monde 2026"]
        for query in queries:
            try:
                r = requests.get(
                    f"https://gnews.io/api/v4/search?q={query}&lang=fr&max=5&apikey={GNEWS_KEY}",
                    timeout=8
                )
                if r.status_code == 200:
                    for a in r.json().get("articles", []):
                        titre = (a.get("title","") or "").lower()
                        if any(m in titre for m in mots_foot):
                            articles.append({
                                "titre": a.get("title",""),
                                "description": a.get("description","") or "",
                                "source": a.get("source",{}).get("name",""),
                                "url": a.get("url",""),
                                "date": (a.get("publishedAt","") or "")[:10]
                            })
            except Exception as e:
                print(f"GNews erreur: {e}")

    if NEWS_KEY and len(articles) < 5:
        queries = ["football coupe monde 2026", "mercato transfert football 2026"]
        for query in queries:
            try:
                r = requests.get(
                    f"https://newsapi.org/v2/everything?q={query}&language=fr&sortBy=publishedAt&pageSize=5&apiKey={NEWS_KEY}",
                    timeout=8
                )
                if r.status_code == 200:
                    for a in r.json().get("articles", []):
                        titre = (a.get("title","") or "").lower()
                        if any(m in titre for m in mots_foot):
                            articles.append({
                                "titre": a.get("title",""),
                                "description": a.get("description","") or "",
                                "source": a.get("source",{}).get("name",""),
                                "url": a.get("url",""),
                                "date": (a.get("publishedAt","") or "")[:10]
                            })
            except:
                pass

    seen = set()
    unique = []
    for a in articles:
        if a["titre"] and a["titre"] not in seen:
            seen.add(a["titre"])
            unique.append(a)
    unique.sort(key=lambda x: x["date"], reverse=True)
    print(f"✅ {len(unique)} articles récupérés")
    return unique[:20]

def get_info_hors_saison(comp_code, comp_nom):
    debut = DEBUT_SAISON.get(comp_code, "")
    infos = []
    if debut:
        infos.append(f"📅 Reprise saison : {debut}")
    if GNEWS_KEY:
        try:
            query = f"transfert mercato {comp_nom} 2026"
            r = requests.get(
                f"https://gnews.io/api/v4/search?q={query}&lang=fr&max=5&apikey={GNEWS_KEY}",
                timeout=5
            )
            if r.status_code == 200:
                for a in r.json().get("articles", [])[:5]:
                    t = a.get("title","")
                    if t:
                        infos.append(f"🔄 {t[:120]}")
        except:
            pass
    if NEWS_KEY and len(infos) < 3:
        try:
            query = f"transfert mercato {comp_nom} 2026"
            r = requests.get(
                f"https://newsapi.org/v2/everything?q={query}&language=fr&sortBy=publishedAt&pageSize=3&apiKey={NEWS_KEY}",
                timeout=5
            )
            if r.status_code == 200:
                for a in r.json().get("articles", [])[:3]:
                    t = a.get("title","")
                    if t:
                        infos.append(f"🔄 {t[:120]}")
        except:
            pass
    if len(infos) < 2:
        infos.append(f"🔄 Mercato d'été 2026 en cours")
    return infos

def get_classement(comp_code):
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{comp_code}/standings",
            headers=HEADERS, timeout=8
        )
        if r.status_code == 200:
            result = []
            standings = r.json().get("standings", [])
            for standing in standings:
                group = standing.get("group", "")
                for t in standing.get("table", [])[:4 if len(standings) > 1 else 20]:
                    result.append({
                        "pos": t["position"],
                        "equipe": t["team"]["shortName"] or t["team"]["name"],
                        "team_id": t["team"]["id"],
                        "pts": t["points"],
                        "j": t["playedGames"],
                        "g": t["won"],
                        "n": t["draw"],
                        "p": t["lost"],
                        "bp": t["goalsFor"],
                        "bc": t["goalsAgainst"],
                        "groupe": group.replace("GROUP_","") if group else ""
                    })
            return result
    except:
        pass
    return []

def get_buteurs(comp_code):
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{comp_code}/scorers?limit=10",
            headers=HEADERS, timeout=8
        )
        if r.status_code == 200:
            return [{
                "joueur": s["player"]["name"],
                "equipe": s["team"]["shortName"] or s["team"]["name"],
                "buts": s["goals"],
                "passes": s.get("assists", 0) or 0
            } for s in r.json().get("scorers", [])[:10]]
    except:
        pass
    return []

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
            historique["matchs"].append({
                "id": m["id"],
                "domicile": m["domicile"],
                "exterieur": m["exterieur"],
                "score": m["score"],
                "date": m["date"],
                "ligue": m["ligue"],
                "oracle_signal": m["oracle"].get("signal",""),
                "oracle_proba_dom": m["oracle"].get("proba_dom",0),
                "oracle_proba_ext": m["oracle"].get("proba_ext",0),
                "favori": m["oracle"].get("favori",""),
                "forme_dom": m["stats_dom"].get("forme",""),
                "forme_ext": m["stats_ext"].get("forme","")
            })
            ajoutes += 1
    historique["total_matchs"] = len(historique["matchs"])
    historique["derniere_maj"] = TODAY
    print(f"📚 Historique : {historique['total_matchs']} matchs ({ajoutes} nouveaux)")
    return historique

# ==========================================
# CORE
# ==========================================
vaticin_data = {
    "mise_a_jour": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "news_globales": [],
    "ligues": []
}

historique = charger_historique()
tous_matchs = []
meteo_cache = {}
forme_cache = {}

vaticin_data["news_globales"] = get_news_globales()

for comp_code, comp_nom in COMPETITIONS.items():
    print(f"📡 {comp_nom}...")
    ligue_data = {
        "code": comp_code,
        "nom": comp_nom,
        "meteo": "",
        "classement": [],
        "buteurs": [],
        "matchs": [],
        "hors_saison": False,
        "infos_hors_saison": []
    }

    ville = STADES.get(comp_code, "Paris")
    if ville not in meteo_cache:
        meteo_cache[ville] = get_meteo(ville)
    ligue_data["meteo"] = meteo_cache[ville]

    # ✅ Classement et buteurs TOUJOURS récupérés (même hors saison)
    classement = get_classement(comp_code)
    ligue_data["classement"] = classement
    positions = {row["team_id"]: row["pos"] for row in classement}
    total_equipes = max(len(classement), 4)
    ligue_data["buteurs"] = get_buteurs(comp_code)

    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{comp_code}/matches",
            headers=HEADERS, timeout=10
        )
        if r.status_code == 200:
            all_matchs = r.json().get("matches", [])
            live = [m for m in all_matchs if m["status"] in ["LIVE","IN_PLAY"]]
            a_venir = [m for m in all_matchs
                      if m["status"] in ["TIMED","SCHEDULED"]
                      and m["utcDate"][:10] <= DANS_7J][:6]
            termines = [m for m in all_matchs if m["status"] == "FINISHED"][-5:]
            matchs_selec = live + termines + a_venir

            # ✅ Hors saison : on marque mais on continue quand même
            if not matchs_selec and comp_code != "WC":
                ligue_data["hors_saison"] = True
                ligue_data["infos_hors_saison"] = get_info_hors_saison(comp_code, comp_nom)
                # PAS de continue ici — on sauvegarde classement et buteurs !
            else:
                for m in matchs_selec:
                    home = m["homeTeam"]["shortName"] or m["homeTeam"]["name"]
                    away = m["awayTeam"]["shortName"] or m["awayTeam"]["name"]
                    home_id = m["homeTeam"]["id"]
                    away_id = m["awayTeam"]["id"]

                    if home_id not in forme_cache:
                        forme_cache[home_id] = get_forme(home_id)
                    if away_id not in forme_cache:
                        forme_cache[away_id] = get_forme(away_id)

                    stats_dom = forme_cache[home_id]
                    stats_ext = forme_cache[away_id]
                    pos_dom = positions.get(home_id)
                    pos_ext = positions.get(away_id)
                    oracle = calculer_oracle(stats_dom, stats_ext, pos_dom, pos_ext, total_equipes)

                    sh = m["score"]["fullTime"]["home"]
                    sa = m["score"]["fullTime"]["away"]
                    score_txt = f"{sh}-{sa}" if sh is not None else "VS"
                    groupe = (m.get("group") or "").replace("GROUP_","")
                    analyse = generer_analyse(home, away, oracle, stats_dom, stats_ext, m["status"], score_txt, groupe)

                    match_data = {
                        "id": m["id"],
                        "domicile": home,
                        "exterieur": away,
                        "heure": m.get("utcDate",""),
                        "score": score_txt,
                        "statut": m.get("status"),
                        "groupe": groupe,
                        "stats_dom": stats_dom,
                        "stats_ext": stats_ext,
                        "oracle": oracle,
                        "analyse": analyse,
                        "meteo": ligue_data["meteo"],
                        "ligue": comp_nom,
                        "date": m.get("utcDate","")[:10]
                    }
                    ligue_data["matchs"].append(match_data)
                    tous_matchs.append(match_data)

    except Exception as e:
        print(f"❌ {comp_code}: {e}")

    vaticin_data["ligues"].append(ligue_data)

with open("ligues.json", "w", encoding="utf-8") as f:
    json.dump(vaticin_data, f, indent=2, ensure_ascii=False)
print("✅ ligues.json mis à jour")

historique = sauvegarder_historique(historique, tous_matchs)
with open("historique.json", "w", encoding="utf-8") as f:
    json.dump(historique, f, indent=2, ensure_ascii=False)
print("✅ historique.json mis à jour")

print("=== VATICIN ENGINE — TERMINÉ ===")
