import os
import json
import random
import requests
from datetime import datetime

FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# Matrice de traduction intégrée pour éviter les requêtes lentes
TRANSLATIONS = {
    "CIBLE": {"fr": "CIBLE", "en": "TARGET", "es": "OBJETIVO", "pt": "ALVO", "ar": "هدف", "sw": "SHABAHA"},
    "ALERTE": {"fr": "ALERTE", "en": "ALERT", "es": "ALERTA", "pt": "ALERTA", "ar": "تحذير", "sw": "TAHADHARI"},
    "BRAQUAGE": {"fr": "BRAQUAGE", "en": "HEIST", "es": "ATRACO", "pt": "ESTOURO", "ar": "سرقة", "sw": "UPORAJI"},
    "VIC_HOME": {"fr": "Victoire {}", "en": "{} Win", "es": "Victoria {}", "pt": "Vitória do {}", "ar": "فوز {}", "sw": "Ushindi {}"},
    "VIC_AWAY": {"fr": "Victoire {}", "en": "{} Win", "es": "Victoria {}", "pt": "Vitória do {}", "ar": "فوز {}", "sw": "Ushindi {}"},
    "COUV": {"fr": "Nul ou {}", "en": "Draw or {}", "es": "Empate o {}", "pt": "Empate ou {}", "ar": "تعادل أو {}", "sw": "Sare au {}"},
    "IMPACT_SAFE": {
        "fr": "Dynamique insolente de {} à domicile.", "en": "Unstoppable form for {} at home.", "es": "Forma imparable de {} en casa.",
        "pt": "Forma incrível do {} em casa.", "ar": "أداء مرعب لـ {} على أرضه.", "sw": "Fomu ya hatari ya {} nyumbani."
    },
    "IMPACT_WARN": {
        "fr": "Historique serré. Match à haute tension.", "en": "Tight head-to-head. High tension match.", "es": "Historial ajustado. Partido de alta tensión.",
        "pt": "Histórico equilibrado. Jogo de alta tensão.", "ar": "تاريخ مواجهات معقد. مباراة مشحونة.", "sw": "Historia ni ngumu. Mechi ina upinzani mkubwa."
    },
    "IMPACT_RISK": {
        "fr": "Alerte rotation d'effectif ou surprise tactique.", "en": "Squad rotation warning or tactical surprise.", "es": "Alerta de rotación de plantilla o sorpresa táctica.",
        "pt": "Aviso de rotação de elenco ou tática nova.", "ar": "تحذير من تدوير التشكيلة.", "sw": "Tahadhari ya mabadiliko ya kikosi."
    },
    "COMMU_SAFE": {"fr": "85% misent le favori", "en": "85% back the favorite", "es": "85% apoyan al favorito", "pt": "85% apoiam o favorito", "ar": "85% يدعمون المرشح", "sw": "85% wanampa nafasi mshindi"},
    "COMMU_WARN": {"fr": "Avis très partagés", "en": "Highly divided opinions", "es": "Opiniones muy divididas", "pt": "Opiniões muito divididas", "ar": "آراء منقسمة جداً", "sw": "Maoni yamegawanyika sana"},
    "COMMU_RISK": {"fr": "Cote folle tentée", "en": "Crazy odds attempted", "es": "Cuota loca intentada", "pt": "Odd alta tentada", "ar": "مخاطرة برهان عالي", "sw": "Utabiri wa mechi ngumu"},
    "PUNCH_SAFE": {"fr": "C'est un cadeau.", "en": "It's a gift.", "es": "Es un regalo.", "pt": "É um presente.", "ar": "إنها هدية.", "sw": "Hii ni zawadi."},
    "PUNCH_WARN": {"fr": "Attention au piège.", "en": "Watch out for the trap.", "es": "Cuidado con la trampa.", "pt": "Cuidado com a armadilha.", "ar": "احذر من الفخ.", "sw": "Angalia mtego."},
    "PUNCH_RISK": {"fr": "Le hold-up se prépare.", "en": "The heist is loading.", "es": "El atraco se está preparando.", "pt": "O roubo está a caminho.", "ar": "المفاجأة قادمة.", "sw": "Uporaji unakuja."}
}

def fetch_data():
    all_signals = []
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    fb_url = f"https://api.football-data.org/v4/matches?dateFrom={today}&dateTo={today}"
    fb_headers = {"X-Auth-Token": FOOTBALL_API_KEY} if FOOTBALL_API_KEY else {}
    news_url = f"https://newsapi.org/v2/everything?q=football&from={today}&sortBy=popularity&apiKey={NEWS_API_KEY}"
    
    try:
        fb_res = requests.get(fb_url, headers=fb_headers, timeout=10).json()
        matches = fb_res.get("matches", [])
    except:
        matches = []

    news_headline = "Vatican Engine Connected."
    try:
        if NEWS_API_KEY:
            news_res = requests.get(news_url, timeout=10).json()
            articles = news_res.get("articles", [])
            if articles:
                news_headline = articles[0].get("title", news_headline)
    except:
        pass

    for m in matches:
        comp_code = m.get("competition", {}).get("code")
        if comp_code not in ["PL", "PD", "FL1", "CL"]: 
            continue
            
        home = m.get("homeTeam", {}).get("shortName") or m.get("homeTeam", {}).get("name")
        away = m.get("awayTeam", {}).get("shortName") or m.get("awayTeam", {}).get("name")
        match_time = m.get("utcDate", "")[11:16]
        
        pct = random.randint(35, 92)
        
        if pct >= 75:
            sig_type, b_key, p_key, i_key, c_key, pu_key = "safe", "CIBLE", "VIC_HOME", "IMPACT_SAFE", "COMMU_SAFE", "PUNCH_SAFE"
        elif pct >= 55:
            sig_type, b_key, p_key, i_key, c_key, pu_key = "warning", "ALERTE", "COUV", "IMPACT_WARN", "COMMU_WARN", "PUNCH_WARN"
        else:
            sig_type, b_key, p_key, i_key, c_key, pu_key = "risk", "BRAQUAGE", "VIC_AWAY", "IMPACT_RISK", "COMMU_RISK", "PUNCH_RISK"

        languages = ["fr", "en", "es", "pt", "ar", "sw"]
        badge_langs = TRANSLATIONS[b_key]
        
        pred_langs = {}
        for l in languages:
            team_param = away if b_key == "COUV" else (home if b_key == "CIBLE" else away)
            pred_langs[l] = TRANSLATIONS[p_key][l].format(team_param)

        impact_langs = {}
        for l in languages:
            impact_langs[l] = TRANSLATIONS[i_key][l].format(home if b_key == "CIBLE" else "") if "{}" in TRANSLATIONS[i_key][l] else TRANSLATIONS[i_key][l]
            if len(all_signals) == 0 and l == "en":
                impact_langs[l] = f"{news_headline} ({home} v {away})"

        all_signals.append({
            "home": home, "away": away, "time": match_time, "type": sig_type, "pct": pct,
            "badge": badge_langs, "prediction": pred_langs, "impact": impact_langs,
            "chat_flash": {"tendence_commu": TRANSLATIONS[c_key], "last_punchline": TRANSLATIONS[pu_key]}
        })
        
    return all_signals

def main():
    data = fetch_data()
    with open("ligues.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Robot OK. {len(data)} matchs chargés.")

if __name__ == "__main__":
    main()
