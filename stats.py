import requests
import os
import datetime

# --- AYARLAR ---
USERNAME = "fatihpnrbs"
TOKEN = os.environ.get("GH_TOKEN") # Token'ı GitHub Secrets'tan alacağız

# --- RENKLER & TASARIM ---
THEME = {
    "bg": "#1a1b27",          # Arka plan rengi
    "text": "#7aa2f7",        # Ana metin rengi (başlık)
    "stat_text": "#c0caf5",   # İstatistik metin rengi
    "icon": "#bb9af7",        # İkon rengi
    "streak": "#ff9e64",      # Streak ateş rengi
    "ring_bg": "#24283b",     # Halka arka planı
    "border": "#414868",      # Çerçeve rengi
    "grade_S": "#9ece6a",     # S notu rengi (Yeşil)
    "grade_A": "#7dcfff",     # A notu rengi (Mavi)
    "grade_B": "#e0af68",     # B notu rengi (Sarı)
}

# --- FONKSİYONLAR ---

def get_data():
    """REST ve GraphQL API'den tüm verileri çeker."""
    headers = {"Authorization": f"bearer {TOKEN}"}
    
    # 1. Temel İstatistikler (REST API)
    rest_resp = requests.get(f"https://api.github.com/users/{USERNAME}", headers=headers)
    rest_data = rest_resp.json()

    # 2. Streak ve Detaylı Veriler için GraphQL Sorgusu
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
          totalRepositoryContributions
        }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
          totalCount
          nodes {
            stargazers {
              totalCount
            }
          }
        }
      }
    }
    """ % USERNAME
    
    gql_resp = requests.post('https://api.github.com/graphql', json={'query': graphql_query}, headers=headers)
    gql_data = gql_resp.json()['data']['user']

    # Toplam Yıldız Sayısını Hesapla
    total_stars = sum(repo['stargazers']['totalCount'] for repo in gql_data['repositories']['nodes'])

    # Streak Hesapla
    streak = calculate_streak(gql_data['contributionsCollection']['contributionCalendar']['weeks'])

    # Tüm veriyi birleştir
    return {
        "username": USERNAME,
        "stars": total_stars,
        "commits": gql_data['contributionsCollection']['totalCommitContributions'],
        "prs": gql_data['contributionsCollection']['totalPullRequestContributions'],
        "issues": gql_data['contributionsCollection']['totalIssueContributions'],
        "contrib_to": rest_data.get('public_repos', 0), # Basitlik için public repo sayısını aldık
        "followers": rest_data.get('followers', 0),
        "streak": streak,
    }

def calculate_streak(weeks):
    """Güncel katkı serisini (streak) hesaplar."""
    days = []
    for week in weeks:
        days.extend(week['contributionDays'])
    
    days.reverse() # Bugünden geriye doğru sırala
    
    streak = 0
    today = datetime.date.today()
    
    # Dün veya bugün katkı yapıldıysa seri devam eder
    streak_broken = False
    
    for i, day in enumerate(days):
        day_date = datetime.datetime.strptime(day['date'], "%Y-%m-%d").date()
        count = day['contributionCount']
        
        # İlk gün kontrolü (bugün veya dün)
        if i == 0:
            if day_date == today and count == 0:
                # Bugün henüz katkı yok, düne bakılacak, seri bozulmuş sayılmaz
                pass 
            elif day_date != today and (today - day_date).days > 1:
                 # En son katkı dünden de önceyse seri bitmiştir.
                 break

        if count > 0:
            streak += 1
        elif count == 0 and (today - day_date).days > 0:
            # Dünden önceki bir günde katkı 0 ise seri biter
             if i > 0:
                 break
             elif i == 0 and (today - day_date).days == 1 and count ==0 :
                  # Dün katkı yoksa seri bitmiştir.
                  break

    return streak

def calculate_grade(data):
    """İstatistiklere göre bir not ve renk belirler."""
    # Basit bir puanlama formülü (istediğin gibi değiştirebilirsin)
    score = (data['commits'] * 2) + (data['prs'] * 5) + (data['issues'] * 3) + (data['stars'] * 10) + (data['followers'] * 2)
    
    if score > 5000: grade, color, progress = "A++", THEME['grade_S'], 100
    elif score > 2500: grade, color, progress = "A+", THEME['grade_A'], 85
    elif score > 1000: grade, color, progress = "A", THEME['grade_A'], 70
    elif score > 500: grade, color, progress = "B+", THEME['grade_B'], 55
    else: grade, color, progress = "B", THEME['grade_B'], 40
    
    return grade, color, progress

def create_svg(data):
    grade, grade_color, progress_percent = calculate_grade(data)
    
    # Halka İlerleme Hesabı
    radius = 40
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference * (1 - progress_percent / 100)

    svg = f"""
    <svg width="550" height="220" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Ubuntu, sans-serif">
        <style>
            .header {{ font-weight: 700; font-size: 20px; fill: {THEME['text']}; }}
            .stat-label {{ font-size: 14px; fill: {THEME['stat_text']}; font-weight: 500; }}
            .stat-value {{ font-size: 14px; fill: {THEME['text']}; font-weight: 700; }}
            .icon {{ fill: {THEME['icon']}; }}
            .streak-icon {{ fill: {THEME['streak']}; }}
            .streak-value {{ font-size: 32px; font-weight: 800; fill: {THEME['text']}; }}
            .streak-label {{ font-size: 12px; fill: {THEME['stat_text']}; font-weight: 600; letter-spacing: 1px; }}
            .grade-text {{ font-size: 28px; font-weight: 800; fill: {grade_color}; }}
            .box {{ fill: {THEME['bg']}; stroke: {THEME['border']}; stroke-width: 1.5px; rx: 15px; }}
            .progress-ring-bg {{ fill: none; stroke: {THEME['ring_bg']}; stroke-width: 8; }}
            .progress-ring-bar {{ fill: none; stroke: {grade_color}; stroke-width: 8; stroke-linecap: round; transition: stroke-dashoffset 0.5s ease-in-out; }}
        </style>
        
        <rect x="1" y="1" width="548" height="218" class="box"/>
        
        <text x="30" y="40" class="header">@{data['username']}'in GitHub İstatistikleri</text>

        <g transform="translate(30, 70)">
            <g transform="translate(0, 0)">
                <svg class="icon" width="16" height="16" viewBox="0 0 16 16"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>
                <text x="25" y="13" class="stat-label">Toplam Yıldız:</text>
                <text x="120" y="13" class="stat-value">{data['stars']}</text>
            </g>
            <g transform="translate(0, 28)">
                <svg class="icon" width="16" height="16" viewBox="0 0 16 16"><path d="M11.93 8.5a4.002 4.002 0 01-7.86 0H.75a.75.75 0 010-1.5h3.32a4.002 4.002 0 017.86 0h3.32a.75.75 0 010 1.5h-3.32zM8 5.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5z"/></svg>
                <text x="25" y="13" class="stat-label">Toplam Commit:</text>
                <text x="135" y="13" class="stat-value">{data['commits']}</text>
            </g>
             <g transform="translate(0, 56)">
                <svg class="icon" width="16" height="16" viewBox="0 0 16 16"><path d="M1.5 3.25a2.25 2.25 0 113 2.122V6.5h9.75a.75.75 0 010 1.5H4.5v1.128a2.25 2.25 0 11-3 2.122v-8zM3.75 2a.75.75 0 100 1.5.75.75 0 000-1.5zM2.25 10a.75.75 0 101.5 0 .75.75 0 00-1.5 0zm11.25-5.5a2.25 2.25 0 110 4.5 2.25 2.25 0 010-4.5zM13.5 6a.75.75 0 100 1.5.75.75 0 000-1.5z"/></svg>
                <text x="25" y="13" class="stat-label">Toplam PR:</text>
                <text x="120" y="13" class="stat-value">{data['prs']}</text>
            </g>
            <g transform="translate(0, 84)">
                <svg class="icon" width="16" height="16" viewBox="0 0 16 16"><path d="M8 8a3 3 0 100-6 3 3 0 000 6zm2-3a2 2 0 11-4 0 2 2 0 014 0zm4 8c0 1.1-1.567 2-5 2S2 14.1 2 13c0-1.224 1.688-2.5 5-2.5 3.312 0 5 1.276 5 2.5zM8 11.5c-2.952 0-4 1.047-4 1.5 0 .453 1.048 1.5 4 1.5 2.952 0 4-1.047 4-1.5 0-.453-1.048-1.5-4-1.5z"/></svg>
                <text x="25" y="13" class="stat-label">Takipçiler:</text>
                <text x="120" y="13" class="stat-value">{data['followers']}</text>
            </g>
        </g>

        <line x1="220" y1="60" x2="220" y2="180" stroke="{THEME['ring_bg']}" stroke-width="1"/>

        <g transform="translate(280, 70)">
            <svg class="streak-icon" x="15" y="-10" width="40" height="40" viewBox="0 0 24 24">
                <path d="M12 23c6.075 0 11-4.925 11-11S18.075 1 12 1 1 5.925 1 12s4.925 11 11 11zm0-22C17.523 2 22 6.477 22 12s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z" fill-opacity="0.2"/> <path d="M15.64 14.732a3.425 3.425 0 01-1.23 2.082 3.426 3.426 0 01-3.052.54c.49-.664.988-1.88.477-2.99-1.025-2.228-3.068-2.49-2.85-5.16.12-1.45 1.028-2.555 1.965-3.393C12.845 4.076 13.35 2 13.35 2s.964 1.844.588 4.098c-.377 2.256-2.297 3.366-2.297 3.366s1.134.118 2.013 1.056c.88.938 1.463 2.255 1.986 4.212zM9.5 18.5l.006-.001c-.002.001-.004.001-.006.001z"/> </svg>
            <text x="35" y="65" class="streak-value" text-anchor="middle">{data['streak']}</text>
            <text x="35" y="85" class="streak-label" text-anchor="middle">GÜNLÜK SERİ</text>
        </g>

        <line x1="380" y1="60" x2="380" y2="180" stroke="{THEME['ring_bg']}" stroke-width="1"/>

        <g transform="translate(450, 120)">
            <circle class="progress-ring-bg" cx="0" cy="0" r="{radius}"/>
            <circle class="progress-ring-bar" cx="0" cy="0" r="{radius}" 
                    stroke-dasharray="{circumference}" 
                    stroke-dashoffset="{dash_offset}" 
                    transform="rotate(-90)"/>
            <text x="0" y="10" class="grade-text" text-anchor="middle">{grade}</text>
        </g>
    </svg>
    """
    
    with open("my-custom-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)

# --- ANA BLOG ---
if __name__ == "__main__":
    if not TOKEN:
        print("HATA: GH_TOKEN environment variable'ı bulunamadı!")
        exit(1)
    
    print("Veriler çekiliyor...")
    stats_data = get_data()
    print(f"Veriler alındı: {stats_data}")
    
    print("SVG oluşturuluyor...")
    create_svg(stats_data)
    print("my-custom-stats.svg başarıyla oluşturuldu!")
