import requests

# 台灣 4/27 的比賽 = 美國東部 4/26
GAME_DATE = "20260426"
ESPN_URL = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={GAME_DATE}"

TEAM_MAP = {
    "Toronto Raptors":          "暴龍",
    "Cleveland Cavaliers":      "騎士",
    "Portland Trail Blazers":   "拓荒者",
    "San Antonio Spurs":        "馬刺",
    "Philadelphia 76ers":       "76人",
    "Boston Celtics":           "塞爾提克",
    "Houston Rockets":          "火箭",
    "Los Angeles Lakers":       "湖人",
}

MATCHES = {
    0: ("暴龍",   "騎士"),
    1: ("拓荒者", "馬刺"),
    2: ("76人",   "塞爾提克"),
    3: ("火箭",   "湖人"),
}

FIRESTORE_URL = (
    "https://firestore.googleapis.com/v1/projects/"
    "gen-lang-client-0737444461/databases/(default)/"
    "documents/game_results/nba_0427"
)

def get_winner(event):
    if event["status"]["type"]["name"] != "STATUS_FINAL":
        return None
    for comp in event["competitions"][0]["competitors"]:
        if comp.get("winner", False):
            return TEAM_MAP.get(comp["team"]["displayName"])
    return None

def main():
    resp = requests.get(ESPN_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = {i: None for i in range(4)}
    for event in data.get("events", []):
        comps = event["competitions"][0]["competitors"]
        team_names = {TEAM_MAP.get(c["team"]["displayName"]) for c in comps}
        for mid, (a, b) in MATCHES.items():
            if team_names == {a, b}:
                winner = get_winner(event)
                if winner:
                    results[mid] = winner
                break

    print("📊 賽果:", results)

    fields = {}
    for i, w in results.items():
        fields[f"r{i}"] = {"stringValue": w} if w else {"nullValue": None}

    mask = "&".join(f"updateMask.fieldPaths=r{i}" for i in range(4))
    r = requests.patch(f"{FIRESTORE_URL}?{mask}", json={"fields": fields}, timeout=10)
    print("✅ 成功" if r.status_code == 200 else f"❌ 錯誤 {r.status_code}: {r.text}")

if __name__ == "__main__":
    main()
