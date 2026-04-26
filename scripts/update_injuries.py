"""
自動更新 4/27 預測網頁的傷兵報告
從 ESPN API 抓最新傷兵狀況並更新 index.html
"""
import re
import requests

# ── 4/27 比賽隊伍 ──────────────────────────────────────
MATCHUPS = [
    ("Toronto Raptors",         "Cleveland Cavaliers",      "暴龍 vs 騎士"),
    ("Philadelphia 76ers",      "Boston Celtics",           "76人 vs 塞爾提克"),
    ("Portland Trail Blazers",  "San Antonio Spurs",        "拓荒者 vs 馬刺"),
    ("Houston Rockets",         "Los Angeles Lakers",       "火箭 vs 湖人"),
]

STATUS_CLASS = {
    "Out":          ("i-out",   "❌"),
    "Doubtful":     ("i-doubt", "⚠️"),
    "Questionable": ("i-q",     "❓"),
    "Day-To-Day":   ("i-q",     "❓"),
}

def fetch_injuries():
    """從 ESPN 抓傷兵報告"""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    try:
        r = requests.get(url, timeout=10)
        return r.json().get("items", [])
    except Exception as e:
        print(f"❌ 傷兵 API 失敗: {e}")
        return []

def build_injury_html(items):
    """產生傷兵報告 HTML"""
    # 建立隊名 → 傷兵清單的對應
    team_injuries = {}
    for item in items:
        team_name = item.get("team", {}).get("displayName", "")
        injuries = item.get("injuries", [])
        notable = []
        for inj in injuries:
            player = inj.get("athlete", {}).get("displayName", "")
            status = inj.get("status", "")
            if status in STATUS_CLASS:
                cls, icon = STATUS_CLASS[status]
                # 取球隊中文簡稱
                team_zh = team_name.split()[-1]  # 取最後一字
                notable.append((cls, icon, player, status, team_zh))
        if notable:
            team_injuries[team_name] = notable

    # 組 HTML
    games_html = ""
    any_injury = False
    for full_a, full_b, label in MATCHUPS:
        inj_a = team_injuries.get(full_a, [])
        inj_b = team_injuries.get(full_b, [])
        all_inj = inj_a + inj_b
        if not all_inj:
            continue
        any_injury = True
        tags = "".join(
            f'<span class="i-tag {cls}">{icon} {player} {status}（{team_zh}）</span>'
            for cls, icon, player, status, team_zh in all_inj
        )
        games_html += f"""
  <div class="injury-game">
    <div class="injury-matchup">{label}</div>
    <div class="injury-list">{tags}</div>
  </div>
"""

    if not any_injury:
        games_html = '\n  <div style="font-size:13px;color:var(--muted)">目前無重大傷兵報告</div>\n'

    return f'<div class="injury-box">\n  <div class="injury-title">🚑 傷兵報告</div>{games_html}</div>'

def update_html(new_injury_html):
    """替換 index.html 中的傷兵報告區塊"""
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # 找到並替換 injury-box 區塊
    pattern = r'<div class="injury-box">.*?</div>\s*(?=\n<a class="codex-link"|\n<div class="name-box")'
    new_content = re.sub(pattern, new_injury_html + "\n", content, flags=re.S)

    if new_content == content:
        print("⚠️  找不到傷兵報告區塊，跳過更新")
        return False

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    return True

def main():
    print("🚑 抓取 ESPN 傷兵報告...")
    items = fetch_injuries()
    if not items:
        print("⚠️  無傷兵資料，保留原有內容")
        return

    print(f"   找到 {len(items)} 隊資料")
    injury_html = build_injury_html(items)

    print("💾 更新 index.html...")
    if update_html(injury_html):
        print("✅ 傷兵報告更新完成")
    else:
        print("❌ 更新失敗")

if __name__ == "__main__":
    main()
