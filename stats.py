import requests
import os
import datetime

# --- AYARLAR ---
USERNAME = "fatihpnrbs"
TOKEN = os.environ.get("GH_TOKEN")

# --- RENKLER & TASARIM ---
THEME = {
    "bg": "#1a1b27",          # Arka plan rengi
    "text": "#7aa2f7",        # Ana metin rengi
    "stat_text": "#c0caf5",   # İstatistik metin rengi
    "icon": "#bb9af7",        # İkon rengi
    "streak": "#ff9e64",      # Streak ateş rengi
    "ring_bg": "#24283b",     # Halka arka planı
    "border": "#414868",      # Çerçeve rengi
    "grade_S": "#9ece6a",     # S notu rengi (Yeşil)
    "grade_A": "#7dcfff",     # A notu rengi (Mavi)
    "grade_B": "#e0af68",     # B notu rengi (Sarı)
}

# --- FONKSİYONLAR (Veri Çekme ve Hesaplama) ---
def get_data():
    headers = {"Authorization": f"bearer {TOKEN}"}
    
    try:
        rest_resp = requests.get(f"https://api.github.com/users/{USERNAME}", headers=headers)
        rest_resp.raise_for_status()
        rest_data = rest_resp.json()
    except requests.exceptions.RequestException as e:
        print(f"REST API Hatası: {e}")
        return None

    graphql_query = """
    query {
      user(login: "%s") {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
        }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
          nodes {
            stargazers {
              totalCount
            }
          }
        }
      }
    }
    """ % USERNAME
    
    try:
        gql_resp = requests.post('https://api.github.com/graphql', json={'query': graphql_query}, headers=headers)
        gql_resp.raise_for_status()
        gql_data = gql_resp.json().get('data', {}).get('user')
        if not gql_data:
             print("GraphQL verisi alınamadı.")
             return None
    except requests.exceptions.RequestException as e:
        print(f"GraphQL API Hatası: {e}")
        return None

    total_stars = sum(repo['stargazers']['totalCount'] for repo in gql_data['repositories']['nodes'])
    streak = calculate_streak(gql_data['contributionsCollection']['contributionCalendar']['weeks'])

    return {
        "username": USERNAME,
        "stars": total_stars,
        "commits": gql_data['contributionsCollection']['totalCommitContributions'],
        "prs": gql_data['contributionsCollection']['totalPullRequestContributions'],
        "issues": gql_data['contributionsCollection']['totalIssueContributions'],
        "followers": rest_data.get('followers', 0),
        "streak": streak,
    }

def calculate_streak(weeks):
    days = []
    for week in weeks:
        days.extend(week['contributionDays'])
    days.reverse()
    
    streak = 0
    today = datetime.date.today()
    
    for i, day in enumerate(days):
        day_date = datetime.datetime.strptime(day['date'], "%Y-%m-%d").date()
        count = day['contributionCount']
        
        if i == 0:
            if day_date == today and count == 0:
                pass 
            elif day_date != today and (today - day_date).days > 1:
                 break
        
        if count > 0:
            streak += 1
        elif count == 0 and (today - day_date).days > 0:
             if i > 0 or (i == 0 and (today - day_date).days == 1):
                  break
    return streak

def calculate_grade(data):
    score = (data['commits'] * 2) + (data['prs'] * 5) + (data['issues'] * 3) + (data['stars'] * 10) + (data['followers'] * 2)
    if score > 5000: grade, color, progress = "A++", THEME['grade_S'], 100
    elif score > 2500: grade, color, progress = "A+", THEME['grade_A'], 85
    elif score > 1000: grade, color, progress = "A", THEME['grade_A'], 70
    elif score > 500: grade, color, progress = "B+", THEME['grade_B'], 55
    else: grade, color, progress = "B", THEME['grade_B'], 40
    return grade, color, progress

# --- YENİ SVG TASARIMI (Başlık ve 3 Blok Düzeni) ---
def create_svg(data):
    grade, grade_color, progress_percent = calculate_grade(data)
    
    WIDTH = 400
    HEIGHT = 160
    
    radius = 30
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference * (1 - progress_percent / 100)

    svg = f"""
    <svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Ubuntu, sans-serif">
        <style>
            .header {{ font-weight: 700; font-size: 18px; fill: {THEME['text']}; text-anchor: middle; }}
            .stat-label {{ font-size: 12px; fill: {THEME['stat_text']}; font-weight: 500; }}
            .stat-value {{ font-size: 12px; fill: {THEME['text']}; font-weight: 700; }}
            .icon {{ fill: {THEME['icon']}; }}
            .streak-icon {{ fill: {THEME['streak']}; }}
            .streak-value {{ font-size: 24px; font-weight: 800; fill: {THEME['text']}; }}
            .streak-label {{ font-size: 10px; fill: {THEME['stat_text']}; font-weight: 600; letter-spacing: 0.5px; }}
            .grade-text {{ font-size: 22px; font-weight: 800; fill: {grade_color}; }}
            .box {{ fill: {THEME['bg']}; stroke: {THEME['border']}; stroke-width: 1px; rx: 10px; }}
            .progress-ring-bg {{ fill: none; stroke: {THEME['ring_bg']}; stroke-width: 6; }}
            .progress-ring-bar {{ fill: none; stroke: {grade_color}; stroke-width: 6; stroke-linecap: round; }}
        </style>
        
        <rect x="0.5" y="0.5" width="{WIDTH-1}" height="{HEIGHT-1}" class="box"/>
        
        <text x="{WIDTH/2}" y="30" class="header">Github İstatistiklerim</text>

        <g transform="translate(25, 60)">
            <g transform="translate(0, 0)">
                <svg class="icon" width="14" height="14" viewBox="0 0 16 16"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>
                <text x="20" y="11" class="stat-label">Yıldızlar:</text>
                <text x="85" y="11" class="stat-value">{data['stars']}</text>
            </g>
            <g transform="translate(0, 22)">
                <svg class="icon" width="14" height="14" viewBox="0 0 16 16"><path d="M11.93 8.5a4.002 4.002 0 01-7.86 0H.75a.75.75 0 010-1.5h3.32a4.002 4.002 0 017.86 0h3.32a.75.75 0 010 1.5h-3.32zM8 5.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5z"/></svg>
                <text x="20" y="11" class="stat-label">Commitler:</text>
                <text x="85" y="11" class="stat-value">{data['commits']}</text>
            </g>
             <g transform="translate(0, 44)">
                <svg class="icon" width="14" height="14" viewBox="0 0 16 16"><path d="M1.5 3.25a2.25 2.25 0 113 2.122V6.5h9.75a.75.75 0 010 1.5H4.5v1.128a2.25 2.25 0 11-3 2.122v-8zM3.75 2a.75.75 0 100 1.5.75.75 0 000-1.5zM2.25 10a.75.75 0 101.5 0 .75.75 0 00-1.5 0zm11.25-5.5a2.25 2.25 0 110 4.5 2.25 2.25 0 010-4.5zM13.5 6a.75.75 0 100 1.5.75.75 0 000-1.5z"/></svg>
                <text x="20" y="11" class="stat-label">PR'lar:</text>
                <text x="85" y="11" class="stat-value">{data['prs']}</text>
            </g>
        </g>

        <line x1="145" y1="50" x2="145" y2="135" stroke="{THEME['ring_bg']}" stroke-width="1"/>

        <g transform="translate(180, 60)">
            <svg class="streak-icon" x="10" y="-5" width="30" height="30" viewBox="0 0 24 24">
                <path d="M12 23c6.075 0 11-4.925 11-11S18.075 1 12 1 1 5.925 1 12s4.925 11 11 11zm0-22C17.523 2 22 6.477 22 12s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z" fill-opacity="0.2"/>
                <path d="M15.64 14.732a3.425 3.425 0 01-1.23 2.082 3.426 3.426 0 01-3.052.54c.49-.664.988-1.88.477-2.99-1.025-2.228-3.068-2.49-2.85-5.16.12-1.45 1.028-2.555 1.965-3.393C12.845 4.076 13.35 2 13.35 2s.964 1.844.588 4.098c-.377 2.256-2.297 3.366-2.297 3.366s1.134.118 2.013 1.056c.88.938 1.463 2.255 1.986 4.212zM9.5 18.5l.006-.001c-.002.001-.004.001-.006.001z"/>
            </svg>
            <text x="25" y="50" class="streak-value" text-anchor="middle">{data['streak']}</text>
            <text x="25" y="65" class="streak-label" text-anchor="middle">GÜNLÜK SERİ</text>
        </g>

        <line x1="270" y1="50" x2="270" y2="135" stroke="{THEME['ring_bg']}" stroke-width="1"/>

        <g transform="translate(335, 92)">
            <circle class="progress-ring-bg" cx="0" cy="0" r="{radius}"/>
            <circle class="progress-ring-bar" cx="0" cy="0" r="{radius}" 
                    stroke-dasharray="{circumference}" 
                    stroke-dashoffset="{dash_offset}" 
                    transform="rotate(-90)"/>
            <text x="0" y="8" class="grade-text" text-anchor="middle">{grade}</text>
        </g>
    </svg>
    """
    
    with open("my-custom-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)

# --- ANA BLOK ---
if __name__ == "__main__":
    if not TOKEN:
        print("HATA: GH_TOKEN environment variable'ı bulunamadı!")
        exit(1)
    
    stats_data = get_data()
    if stats_data:
        create_svg(stats_data)
        print("my-custom-stats.svg başarıyla oluşturuldu!")
    else:
        print("Veri alınamadığı için SVG oluşturulamadı.")
        exit(1)
