import os, requests, base64, json, time

# --- CONFIGURATION ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
# The Gemini API Key is provided by the environment
API_KEY = "" 

def fetch_poster_ai(title):
    """Uses Gemini + Google Search to find the official high-res poster."""
    print(f"   [AI Search] Finding poster for: {title}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Find a direct image URL for the official movie poster of '{title}'. Return ONLY the raw URL string."}]}],
            "tools": [{"google_search": {}}]
        }
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            poster = res.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            if poster.startswith("http"): return poster
    except: pass
    return "https://via.placeholder.com/500x750?text=CineView+Original"

def force_push_github(path, content, msg):
    """Aggressively forces a file update by always retrieving the current SHA."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # Always fetch the SHA to ensure we can overwrite
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
    print("--- 🚀 ULTIMATE ENGINE START ---")
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing!"); return

    # 1. Fetch Abyss Data
    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        resp = requests.get(url, timeout=30)
        items = resp.json().get('items', [])
        print(f"Items detected: {len(items)}")
    except Exception as e:
        print(f"Abyss Error: {e}"); return

    catalog = []

    # 2. Process Items
    for item in items:
        name, iid, is_dir = item.get('name'), item.get('id'), item.get('isDir', False)
        if not iid: continue
        
        poster = fetch_poster_ai(name)
        
        if not is_dir:
            # --- MOVIE (Template: Dhurandhar.html) ---
            path = f"Insider/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Movie"})
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{name}</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"><style>:root {{ --bg-dark: #121212; --surface-dark: #1e1e1e; --accent-main: #00bcd4; --text-light: #e0e0e0; --text-muted: #a0a0a0; }} body {{ background-color: var(--bg-dark); color: var(--text-light); font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }} .video-player-container {{ width: 100%; max-width: 900px; border-radius: 16px; overflow: hidden; box-shadow: 0 15px 50px rgba(0, 0, 0, 0.7); background-color: var(--surface-dark); }} .video-frame-area {{ position: relative; width: 100%; padding-bottom: 56.25%; }} iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }} .player-content-area {{ padding: 20px 30px; }} .player-title {{ font-size: 1.5rem; font-weight: 700; color: #fff; }} .player-metadata {{ font-size: 0.85rem; color: var(--text-muted); display: flex; gap: 25px; }} .player-metadata span:not(:last-child)::after {{ content: "•"; margin-left: 15px; opacity: 0.5; }}</style></head><body><div class="video-player-container"><div class="video-frame-area"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="player-content-area"><div class="player-title">{name}</div><div class="player-metadata"><span>HD Stream</span><span>2025</span><span>CineView Hub</span></div></div></div></body></html>"""
            force_push_github(path, html, f"Sync Movie: {name}")
        else:
            # --- SERIES (Template: got2.html) ---
            path = f"episodes/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Series"})
            f_res = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
            children = f_res.get('items', [])
            ep_js = [{"n": c.get('name'), "v": f"https://short.icu/{c.get('id')}"} for c in children]
            opts = "".join([f'<option value="{i}">E{i+1}: {c.get("name")}</option>' for i, c in enumerate(children)])
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{name}</title><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"></head><body><div class="site-title-banner" style="background:linear-gradient(rgba(0,0,0,0.8),#000),url('{poster}'); background-size:cover; padding:60px 20px; text-align:center;"><h1>{name}</h1><p>{len(children)} Episodes</p></div><main style="max-width:1000px; margin:auto; padding:20px;"><div class="player-wrapper" style="background:#111; border-radius:20px; overflow:hidden;"><iframe id="episode-iframe" style="width:100%; aspect-ratio:16/9; border:none;" allowfullscreen></iframe><div style="padding:20px; display:flex; justify-content:space-between; align-items:center;"><h2 id="current-episode-title">Loading...</h2><select id="episode-select" onchange="ch(this.value);" style="background:#222; color:#fff; padding:10px; border-radius:8px; border:1px solid #444;">{opts}</select></div></div></main><script>const EPS = {json.dumps(ep_js)}; function ch(i){{ const e=EPS[i]; document.getElementById('episode-iframe').src=e.v; document.getElementById('current-episode-title').textContent=e.n; }} ch(0);</script></body></html>"""
            force_push_github(path, html, f"Sync Series: {name}")

    # 3. --- INDEX (Template: index.html with SEARCH) ---
    grid_html = "".join([f'<a href="{c["url"]}" class="movie-link" data-title="{c["name"].lower()}"><div class="movie-card"><div class="movie-poster-container"><img src="{c["img"]}" class="movie-poster" loading="lazy"></div><div class="movie-info"><h3>{c["name"]}</h3><p>{c["type"]} | 2025</p></div></div></a>' for c in catalog])
    index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>🎬 CineView Hub</title><link rel="stylesheet" href="style.css"></head><body><header class="main-header"><div class="logo">CineView</div></header><main><section class="hero-section" style="background:linear-gradient(rgba(0,0,0,0.7),#0f0f1d),url('https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1200'); background-size:cover; text-align:center; padding:80px 20px;"><h1>Discover Your Next Favorite Film</h1><div style="max-width:600px; margin:20px auto; position:relative;"><input type="text" id="sb" placeholder="Search movies..." oninput="sf()" style="width:100%; padding:15px 25px; border-radius:30px; border:none; background:rgba(255,255,255,0.1); backdrop-filter:blur(10px); color:#fff; font-size:1.1rem; outline:none; border:1px solid rgba(255,255,255,0.2);"></div></section><section class="movie-section"><h2 class="section-title">✨ New Library</h2><div class="movie-grid" id="mg">{grid_html}</div></section></main><script>function sf(){{const v=document.getElementById('sb').value.toLowerCase(); const c=document.getElementsByClassName('movie-link'); for(let i=0; i<c.length; i++){{const t=c[i].getAttribute('data-title'); c[i].style.display=t.includes(v)?"block":"none";}}}}</script></body></html>"""
    force_push_github("index.html", index_html, "Force Refresh System")

if __name__ == "__main__":
    main()
