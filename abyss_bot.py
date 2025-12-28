import os, requests, base64, json, time

# --- CONFIGURATION ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
# Gemini API Key provided by the environment for poster research
API_KEY = "" 

def fetch_poster_ai(title):
    """Uses AI + Google Search to find the official theatrical poster."""
    print(f"   [AI Search] Finding poster for: {title}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Find the official direct image URL for the movie/series poster of '{title}'. Return ONLY the raw URL string."
                }]
            }],
            "tools": [{"google_search": {}}]
        }
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            poster = res.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            if poster.startswith("http"): return poster
    except: pass
    return "https://image.tmdb.org/t/p/w500/9F4lPRLjfBjsu0zjWNOZQMa8a4V.jpg" # Chhava fallback

def force_push_github(path, content, msg):
    """Aggressively forces a file update by always retrieving the current SHA."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # Always fetch the SHA to ensure we overwrite regardless of existing content
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
    print("--- 🚀 CINEVIEW TOTAL FORCE-SYNC START ---")
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing!"); return

    # 1. Fetch Abyss Data
    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        resp = requests.get(url, timeout=30)
        items = resp.json().get('items', [])
        print(f"Items detected in Abyss: {len(items)}")
    except Exception as e:
        print(f"Abyss API Error: {e}"); return

    catalog = []

    # 2. Process Every Item (Forcing updates on all)
    for item in items:
        name, iid, is_dir = item.get('name'), item.get('id'), item.get('isDir', False)
        if not iid: continue
        
        poster = fetch_poster_ai(name)
        
        if not is_dir:
            # --- MOVIE (Dhurandhar.html Style) ---
            path = f"Insider/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Movie"})
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{name} - CineView</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"><style>:root {{ --bg: #0a0a0c; --surface: #141418; --accent: #00bcd4; --text: #e0e0e0; }} body {{ background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }} .player-card {{ width: 100%; max-width: 1000px; background: var(--surface); border-radius: 20px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.8), 0 0 10px rgba(0,188,212,0.2); border: 1px solid #222; }} .video-area {{ position: relative; width: 100%; padding-bottom: 56.25%; }} iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }} .details {{ padding: 30px; }} .title {{ font-size: 1.8rem; font-weight: 700; color: #fff; margin-bottom: 10px; }} .meta {{ font-size: 0.9rem; color: #888; display: flex; gap: 20px; }} .meta span::after {{ content: "•"; margin-left: 20px; opacity: 0.3; }} .meta span:last-child::after {{ content: ""; }}</style></head><body><div class="player-card"><div class="video-area"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="details"><div class="title">{name}</div><div class="meta"><span>4K Ultra HD</span><span>2025</span><span>English Audio</span></div></div></div></body></html>"""
            force_push_github(path, html, f"Aggressive Update Movie: {name}")
        else:
            # --- SERIES (got2.html Style) ---
            path = f"episodes/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Series"})
            try:
                f_res = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
                children = f_res.get('items', [])
                ep_js = [{"n": c.get('name'), "v": f"https://short.icu/{c.get('id')}"} for c in children]
                opts = "".join([f'<option value="{i}">Episode {i+1}: {c.get("name")}</option>' for i, c in enumerate(children)])
                html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{name} - CineView</title><style>body{{background:#08080a;color:#fff;font-family:sans-serif;margin:0;}}.banner{{background:linear-gradient(rgba(0,0,0,0.8),#000),url('{poster}');background-size:cover;padding:80px 20px;text-align:center;}}.player-box{{max-width:1100px;margin:auto;padding:20px;background:#111;border-radius:20px;border:1px solid #333;overflow:hidden;}}iframe{{width:100%;aspect-ratio:16/9;border:none;}}.controls{{padding:20px;display:flex;justify-content:space-between;align-items:center;}}select{{background:#222;color:#fff;padding:12px;border-radius:8px;border:1px solid #444;}}</style></head><body><div class="banner"><h1>{name}</h1><p>{len(children)} Episodes Available</p></div><div class="player-box"><iframe id="ifr" src="" allowfullscreen></iframe><div class="controls"><div><h2 id="et">Loading...</h2></div><select id="sel" onchange="ch(this.value)">{opts}</select></div></div><script>const EPS = {json.dumps(ep_js)}; function ch(i){{ const e=EPS[i]; document.getElementById('ifr').src=e.v; document.getElementById('et').textContent=e.n; }} ch(0);</script></body></html>"""
                force_push_github(path, html, f"Aggressive Update Series: {name}")
            except: pass

    # 3. --- INDEX (Search Button & Premium UI) ---
    print("Force-rebuilding homepage...")
    grid_html = "".join([f'<a href="{c["url"]}" class="movie-link" data-title="{c["name"].lower()}"><div class="movie-card"><div class="movie-poster-container"><img src="{c["img"]}" class="movie-poster" loading="lazy"></div><div class="movie-info"><h3>{c["name"]}</h3><p>{c["type"]} | 2025</p></div></div></a>' for c in catalog])
    index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>🎬 CineView Hub</title><link rel="stylesheet" href="style.css"></head><body><header class="main-header"><div class="logo">CineView</div></header><main><section class="hero-section" style="background:linear-gradient(rgba(0,0,0,0.7),#0f0f1d),url('https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1200'); background-size:cover; text-align:center; padding:100px 20px;"><h1>Discover Your Next Favorite Film</h1><div style="max-width:600px; margin:20px auto; position:relative;"><input type="text" id="sb" placeholder="Search library..." oninput="sf()" style="width:100%; padding:18px 25px; border-radius:35px; border:none; background:rgba(255,255,255,0.1); backdrop-filter:blur(15px); color:#fff; font-size:1.1rem; outline:none; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 4px 30px rgba(0,0,0,0.5);"></div></section><section class="movie-section"><h2 class="section-title">✨ New Library</h2><div class="movie-grid" id="mg">{grid_html}</div></section></main><script>function sf(){{const v=document.getElementById('sb').value.toLowerCase(); const c=document.getElementsByClassName('movie-link'); for(let i=0; i<c.length; i++){{const t=c[i].getAttribute('data-title'); c[i].style.display=t.includes(v)?"block":"none";}}}}</script></body></html>"""
    
    force_push_github("index.html", index_html, "Force UI Refresh")
    print("--- 🏁 TOTAL SYNC FINISHED ---")

if __name__ == "__main__":
    main()
