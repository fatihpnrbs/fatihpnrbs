import requests

# Senin kullanıcı adın
USERNAME = "fatihpnrbs"

def get_stats():
    # GitHub API'den veriyi çek
    response = requests.get(f"https://api.github.com/users/{USERNAME}")
    data = response.json()
    return data

def create_svg(data):
    # Basit ve temiz bir tasarım (Dark Mode uyumlu)
    svg_content = f"""
    <svg width="400" height="150" xmlns="http://www.w3.org/2000/svg">
        <style>
            .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #2f80ed; }}
            .stat {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}
            .box {{ fill: #0d1117; stroke: #30363d; stroke-width: 1px; rx: 10px; }}
            .line {{ stroke: #21262d; stroke-width: 1; }}
        </style>
        
        <rect x="1" y="1" width="398" height="148" class="box"/>
        
        <text x="25" y="35" class="header">@{USERNAME} GitHub İstatistikleri</text>
        <line x1="25" y1="50" x2="375" y2="50" class="line"/>

        <text x="25" y="80" class="stat">📦 Public Repos: {data['public_repos']}</text>
        <text x="200" y="80" class="stat">👥 Followers: {data['followers']}</text>
        <text x="25" y="110" class="stat">📅 Katıldı: {data['created_at'][:4]}</text>
        <text x="200" y="110" class="stat">🧬 Public Gists: {data['public_gists']}</text>
    </svg>
    """
    
    # Dosyayı kaydet
    with open("my-custom-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

if __name__ == "__main__":
    stats = get_stats()
    create_svg(stats)
    print("SVG başarıyla oluşturuldu!")
