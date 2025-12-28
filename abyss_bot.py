import os, requests, base64, json, time

# --- CONFIGURATION ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
API_KEY = "" # Gemini API Key provided by the environment

# List of folder/file names to ignore
BLACKLIST = ["recycle bin", "deleted", "trash", "temp", "hidden"]

def fetch_poster_ai(title):
    """Uses AI + Google Search to find a specific official theatrical poster."""
    print(f"   [AI Search] Finding unique poster for: {title}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Find the official direct image URL for the theatrical movie poster of '{title}'. The image must be vertically oriented. Return ONLY the raw URL string starting with http. Do not return the same image for different movies."
                }]
            }],
            "tools": [{"google_search": {}}]
        }
        res = requests.post(url, json=payload, timeout=25)
        if res.status_code == 200:
            poster = res.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            if poster.startswith("http"): return poster
    except: pass
    # Unique fallback using a dynamic placeholder if AI fails
    return f"https://via.placeholder.com/500x750/111/fff?text={title.replace(' ', '+')}"

def force_push_github(path, content, msg):
    """Aggressively forces a file update by always retrieving the current SHA."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    
    payload = {
        "message": msg,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
    }
    if sha: payload["sha"] = sha
    
    res = requests.put(url, headers=headers, json=payload)
    print(f"   [GitHub API] {path} -> {res.status_code}")
    return res.status_code

def main():
    print("--- 🚀 CINEVIEW PREMIUM ENGINE START ---")
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing!"); return

    # 1. Fetch Abyss Data
    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        resp = requests.get(url, timeout=30)
        items = resp.json().get('items', [])
    except Exception as e:
        print(f"Abyss API Error: {e}"); return

    catalog = []

    # 2. Process Every Item
    for item in items:
        name, iid, is_dir = item.get('name'), item.get('id'), item.get('isDir', False)
        if not iid: continue
        
        # EXCLUDE BLACKLISTED ITEMS
        if any(word in name.lower() for word in BLACKLIST):
            print(f"   [Skip] Excluded: {name}")
            continue
        
        poster = fetch_poster_ai(name)
        
        if not is_dir:
            # --- MOVIE (Dhurandhar.html Premium Style) ---
            path = f"Insider/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Movie"})
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{name}</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet"><style>:root {{ --bg: #050507; --surface: #121216; --accent: #00bcd4; }} body {{ background: var(--bg); color: #fff; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }} .card {{ width: 100%; max-width: 950px; background: var(--surface); border-radius: 24px; overflow: hidden; box-shadow: 0 30px 60px rgba(0,0,0,0.6); border: 1px solid #222; }} iframe {{ width: 100%; aspect-ratio: 16/9; border: none; }} .meta {{ padding: 30px; }} .title {{ font-size: 1.8rem; font-weight: 700; color: #fff; }} .badge {{ display: inline-block; padding: 4px 12px; background: rgba(0,188,212,0.1); color: var(--accent); border-radius: 6px; font-size: 0.8rem; font-weight: 600; margin-top: 10px; border: 1px solid var(--accent); }}</style></head><body><div class="card"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe><div class="meta"><div class="title">{name}</div><div class="badge">4K ULTRA HD</div></div></div></body></html>"""
            force_push_github(path, html, f"Premium Movie Sync: {name}")
        else:
            # --- SERIES (got2.html Premium Style) ---
            path = f"episodes/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Series"})
            try:
                f_res = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
                children = f_res.get('items', [])
                ep_js = [{"n": c.get('name'), "v": f"https://short.icu/{c.get('id')}"} for c in children]
                opts = "".join([f'<option value="{i}">Episode {i+1}: {c.get("name")}</option>' for i, c in enumerate(children)])
                html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{name}</title><style>body{{background:#08080a;color:#fff;font-family:sans-serif;margin:0;}}.hero{{background:linear-gradient(rgba(0,0,0,0.85),#08080a),url('{poster}');background-size:cover;padding:80px 20px;text-align:center;}}.p-box{{max-width:1100px;margin:auto;background:#111;border-radius:20px;overflow:hidden;border:1px solid #333;}}iframe{{width:100%;aspect-ratio:16/9;border:none;}}select{{background:#222;color:#fff;padding:12px;border-radius:8px;border:1px solid #444;outline:none;}}</style></head><body><div class="hero"><h1>{name}</h1><p>{len(children)} Episodes Available</p></div><div class="p-box"><iframe id="ifr" src="" allowfullscreen></iframe><div style="padding:20px;display:flex;justify-content:space-between;align-items:center;"><h2 id="et">Select Episode</h2><select id="sel" onchange="ch(this.value)">{opts}</select></div></div><script>const EPS = {json.dumps(ep_js)}; function ch(i){{ const e=EPS[i]; document.getElementById('ifr').src=e.v; document.getElementById('et').textContent=e.n; }} ch(0);</script></body></html>"""
                force_push_github(path, html, f"Premium Series Sync: {name}")
            except: pass

    # 3. --- PREMIUM INDEX ---
    print("Building High-Performance Homepage...")
    grid_html = "".join([f"""
    <a href="{c['url']}" class="movie-link" data-title="{c['name'].lower()}">
        <div class="movie-card">
            <div class="movie-poster-container">
                <img src="{c['img']}" alt="{c['name']}" class="movie-poster" loading="lazy">
                <div class="type-badge">{c['type']}</div>
            </div>
            <div class="movie-info">
                <h3>{c['name']}</h3>
                <p>2025 • High Quality</p>
            </div>
        </div>
    </a>""" for c in catalog])

    index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>🎬 CineView - Premium Hub</title><link rel="stylesheet" href="style.css"><style>
    :root {{ --bg: #050507; --card: #111116; --accent: #00d2ff; }}
    body {{ background: var(--bg); color: #fff; font-family: 'Inter', sans-serif; margin: 0; }}
    .hero-section {{ background: linear-gradient(rgba(0,0,0,0.7), var(--bg)), url('https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1600&q=80'); background-size: cover; padding: 120px 20px; text-align: center; }}
    .search-container {{ max-width: 650px; margin: 30px auto; position: relative; }}
    #sb {{ width: 100%; padding: 20px 35px; border-radius: 50px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); color: #fff; font-size: 1.1rem; outline: none; transition: 0.4s; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }}
    #sb:focus {{ border-color: var(--accent); background: rgba(255,255,255,0.1); box-shadow: 0 0 20px rgba(0,210,255,0.3); }}
    .movie-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 30px; padding: 40px; max-width: 1300px; margin: auto; }}
    .movie-card {{ background: var(--card); border-radius: 20px; overflow: hidden; border: 1px solid #1a1a20; transition: 0.4s; height: 100%; position: relative; }}
    .movie-card:hover {{ transform: translateY(-12px); border-color: var(--accent); box-shadow: 0 15px 40px rgba(0,210,255,0.2); }}
    .movie-poster-container {{ position: relative; width: 100%; aspect-ratio: 2/3; overflow: hidden; }}
    .movie-poster {{ width: 100%; height: 100%; object-fit: cover; transition: 0.5s; }}
    .movie-card:hover .movie-poster {{ transform: scale(1.1); }}
    .type-badge {{ position: absolute; top: 15px; right: 15px; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); color: var(--accent); padding: 5px 12px; border-radius: 8px; font-size: 0.7rem; font-weight: 800; border: 1px solid var(--accent); }}
    .movie-info {{ padding: 20px; }}
    .movie-info h3 {{ margin: 0; font-size: 1rem; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .movie-info p {{ margin: 8px 0 0; font-size: 0.8rem; color: #888; }}
    .movie-link {{ text-decoration: none; }}
    @media (max-width: 600px) {{ .movie-grid {{ grid-template-columns: repeat(2, 1fr); gap: 15px; padding: 15px; }} }}
    </style></head><body>
    <header class="main-header"><div class="logo" style="padding:20px; font-size:1.5rem; font-weight:900; color:var(--accent);">CINEVIEW</div></header>
    <div class="hero-section">
        <h1 style="font-size:3rem; margin:0;">CINEVIEW PREMIUM</h1>
        <div class="search-container">
            <input type="text" id="sb" placeholder="Search movies or series..." oninput="sf()">
        </div>
    </div>
    <main><section class="movie-section"><div class="movie-grid" id="mg">{grid_html}</div></section></main>
    <script>function sf(){{const v=document.getElementById('sb').value.toLowerCase(); const c=document.getElementsByClassName('movie-link'); for(let i=0; i<c.length; i++){{const t=c[i].getAttribute('data-title'); c[i].style.display=t.includes(v)?"block":"none";}}}}</script>
    </body></html>"""
    
    force_push_github("index.html", index_html, "Ultimate UI Refresh & Filter Fix")
    print("--- 🏁 ENGINE SYNC COMPLETE ---")

if __name__ == "__main__":
    main()
