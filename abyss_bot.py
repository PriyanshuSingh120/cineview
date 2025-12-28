import os, requests, base64, json, time

# --- CONFIG ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
# The Gemini API Key is provided automatically in the background
API_KEY = "" 

def fetch_poster_url(title):
    """Uses Gemini + Google Search to find a high-quality movie poster URL."""
    print(f"   [AI] Searching for poster: {title}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Find a high-quality direct image URL for the official theatrical movie poster of '{title}'. Return ONLY the raw URL string starting with http. No text, no markdown."
                }]
            }],
            "tools": [{"google_search": {}}]
        }
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            data = res.json()
            poster = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            if poster.startswith("http"):
                return poster
    except Exception as e:
        print(f"   [AI Error] {e}")
    return "https://via.placeholder.com/500x750?text=CineView"

def push_github(path, content, msg):
    """Pushes or updates a file on GitHub."""
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
    print(f"   [GitHub] {path} -> {res.status_code}")
    return res.status_code

def main():
    print("--- CINEVIEW MASTER SYNC START ---")
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing!"); return

    # 1. Fetch Abyss Resources
    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        resp = requests.get(url, timeout=25)
        items = resp.json().get('items', [])
        print(f"Found {len(items)} items in Abyss.")
    except Exception as e:
        print(f"API Error: {e}"); return

    catalog = []

    # 2. Process Items
    for item in items:
        name = item.get('name', 'Untitled')
        iid = item.get('id')
        is_dir = item.get('isDir', False)
        if not iid: continue

        poster = fetch_poster_url(name)
        
        if not is_dir:
            # MOVIE: Based on Dhurandhar.html
            path = f"Insider/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Movie"})
            
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name} - CineView</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"><style>:root {{ --bg-dark: #121212; --surface-dark: #1e1e1e; --accent-main: #00bcd4; --text-light: #e0e0e0; --text-muted: #a0a0a0; }} body {{ background-color: var(--bg-dark); color: var(--text-light); font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }} .video-player-container {{ width: 100%; max-width: 900px; border-radius: 16px; overflow: hidden; box-shadow: 0 15px 50px rgba(0, 0, 0, 0.7), 0 0 5px rgba(0, 188, 212, 0.4); background-color: var(--surface-dark); transition: transform 0.3s ease; }} .video-frame-area {{ position: relative; width: 100%; padding-bottom: 56.25%; }} .video-frame-area iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }} .player-content-area {{ padding: 20px 30px; background-color: var(--surface-dark); }} .player-title {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 5px; }} .player-metadata {{ font-size: 0.85rem; color: var(--text-muted); display: flex; gap: 25px; }} .player-metadata span:not(:last-child)::after {{ content: "•"; margin-left: 15px; opacity: 0.5; }}</style></head><body><div class="video-player-container"><div class="video-frame-area"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="player-content-area"><div class="player-title">{name}</div><div class="player-metadata"><span>HD Streaming</span><span>2025</span><span>CineView</span></div></div></div></body></html>"""
            push_github(path, html, f"Add Movie: {name}")
            
        else:
            # SERIES: Based on got2.html
            path = f"episodes/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Series"})
            
            f_resp = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
            children = f_resp.get('items', [])
            ep_js = [{"index": i, "name": c.get('name'), "videoUrl": f"https://short.icu/{c.get('id')}"} for i, c in enumerate(children)]
            ep_opts = "".join([f'<option value="{i}">E{i+1}: {c.get("name")}</option>' for i, c in enumerate(children)])

            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name} - CineView</title><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"></head><body><div class="site-title-banner"><h1>{name}</h1><p class="site-details-info">{len(children)} Episodes | CineView Series</p></div><main><section class="episode-page-content"><div class="player-wrapper"><div class="video-container"><iframe id="episode-iframe" src="" allowfullscreen></iframe><div class="player-overlay"></div></div><div class="episode-title-bar"><div class="episode-info-left"><h2 id="current-episode-title">Loading...</h2><span id="current-episode-number"></span></div><div class="episode-selector-dropdown"><select id="episode-select" onchange="changeEpisode(this.value);">{ep_opts}</select></div></div></div></section></main><footer><p>&copy; 2025 CineView</p></footer><script>const EPISODES = {json.dumps(ep_js)}; function changeEpisode(idx) {{ const ep = EPISODES[parseInt(idx)]; if(!ep) return; document.getElementById('episode-iframe').src = ep.videoUrl; document.getElementById('current-episode-title').textContent = ep.name; document.getElementById('current-episode-number').textContent = `Episode ${{parseInt(idx)+1}} of ${{EPISODES.length}}`; }} document.addEventListener('DOMContentLoaded', () => changeEpisode(0));</script></body></html>"""
            push_github(path, html, f"Add Series: {name}")

    # 3. Homepage (index.html) based on your provided index.html
    grid_html = "".join([f'<a href="{c["url"]}" class="movie-link"><div class="movie-card"><div class="movie-poster-container"><img src="{c["img"]}" class="movie-poster" loading="lazy"></div><div class="movie-info"><h3>{c["name"]}</h3><p>{c["type"]} | 2025</p></div></div></a>' for c in catalog])
    
    index_full = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>🎬 CineView - Free Movie Hub</title><link rel="stylesheet" href="style.css"></head><body><header class="main-header"><div class="logo">CineView</div><nav class="nav-links"><a href="/">Home</a><a href="/movies/">Movies</a></nav></header><main><section class="hero-section"><h1 class="hero-title">Discover Your Next Favorite Film</h1></section><section class="movie-section"><h2 class="section-title">✨ New Uploads</h2><div class="movie-grid">{grid_html}</div></section></main><footer><p>&copy; 2025 CineView. All rights reserved.</p></footer></body></html>"""
    
    push_github("index.html", index_full, "Full Layout Update")
    print("--- SYNC COMPLETE ---")

if __name__ == "__main__":
    main()    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    
    payload = {
        "message": msg,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
    }
    if sha: payload["sha"] = sha
    
    res = requests.put(url, headers=headers, json=payload)
    print(f"   [GitHub] {path} -> {res.status_code}")
    return res.status_code

def main():
    print("--- STARTING CINEVIEW SYNC ---")
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing!"); return

    # 1. Fetch Resources
    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        resp = requests.get(url, timeout=20)
        items = resp.json().get('items', [])
        print(f"Found {len(items)} items in Abyss.")
    except Exception as e:
        print(f"API Error: {e}"); return

    catalog = []

    # 2. Process Items
    for item in items:
        name = item.get('name', 'Untitled')
        iid = item.get('id')
        is_dir = item.get('isDir', False)
        
        if not iid: continue

        # AUTO-FETCH POSTER
        poster = fetch_poster_url(name)
        
        if not is_dir:
            # MOVIE: Using Dhurandhar.html Template
            path = f"Insider/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Movie"})
            
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name} - CineView</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"><style>:root {{ --bg-dark: #121212; --surface-dark: #1e1e1e; --accent-main: #00bcd4; --text-light: #e0e0e0; --text-muted: #a0a0a0; }} body {{ background-color: var(--bg-dark); color: var(--text-light); font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }} .video-player-container {{ width: 100%; max-width: 900px; border-radius: 16px; overflow: hidden; box-shadow: 0 15px 50px rgba(0, 0, 0, 0.7), 0 0 5px rgba(0, 188, 212, 0.4); background-color: var(--surface-dark); }} .video-frame-area {{ position: relative; width: 100%; padding-bottom: 56.25%; }} .video-frame-area iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }} .player-content-area {{ padding: 20px 30px; background-color: var(--surface-dark); }} .player-title {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 5px; }} .player-metadata {{ font-size: 0.85rem; color: var(--text-muted); display: flex; gap: 25px; }}</style></head><body><div class="video-player-container"><div class="video-frame-area"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="player-content-area"><div class="player-title">{name}</div><div class="player-metadata"><span>HD Streaming</span><span>2025</span><span>CineView Hub</span></div></div></div></body></html>"""
            push_github(path, html, f"Add Movie: {name}")
            
        else:
            # SERIES: Using got2.html Template
            path = f"episodes/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Series"})
            
            # Fetch Episodes
            f_resp = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
            children = f_resp.get('items', [])
            
            ep_js_array = []
            ep_options = ""
            for idx, c in enumerate(children):
                ep_js_array.append({
                    "index": idx,
                    "name": c.get('name'),
                    "videoUrl": f"https://short.icu/{c.get('id')}",
                    "description": f"Streaming episode: {c.get('name')}"
                })
                ep_options += f'<option value="{idx}">E{idx+1}: {c.get("name")}</option>'

            # Doubled {{ }} are used below to tell Python these are literal braces for JS
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name} - CineView</title><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"></head><body><div class="site-title-banner"><h1>{name}</h1><p class="site-details-info">{len(children)} Episodes | CineView Original</p></div><main><section class="episode-page-content"><div class="player-wrapper"><div class="video-container"><iframe id="episode-iframe" src="" allowfullscreen></iframe></div><div class="episode-title-bar"><div class="episode-info-left"><h2 id="current-episode-title">Episode 1</h2><span id="current-episode-number">Loading...</span></div><div class="episode-selector-dropdown"><select id="episode-select" onchange="changeEpisode(this.value);">{ep_options}</select></div></div></div></section></main><script>const EPISODES = {json.dumps(ep_js_array)}; function changeEpisode(i) {{ const e = EPISODES[parseInt(i)]; if(!e) return; document.getElementById('episode-iframe').src = e.videoUrl; document.getElementById('current-episode-title').textContent = e.name; document.getElementById('current-episode-number').textContent = `Episode ${{parseInt(i)+1}} of ${{EPISODES.length}}`; }} document.addEventListener('DOMContentLoaded', () => changeEpisode(0));</script></body></html>"""
            push_github(path, html, f"Add Series: {name}")

    # 3. Build Homepage (index.html)
    grid_html = ""
    for c in catalog:
        grid_html += f"""
        <a href="{c['url']}" class="movie-link">
            <div class="movie-card">
                <div class="movie-poster-container">
                    <img src="{c['img']}" alt="{c['name']}" class="movie-poster" loading="lazy">
                </div>
                <div class="movie-info">
                    <h3>{c['name']}</h3>
                    <p>{c['type']} | 2025 | CineView</p>
                </div>
            </div>
        </a>"""

    index_full = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>🎬 CineView - Hub</title><link rel="stylesheet" href="style.css"></head><body><header class="main-header"><div class="logo">CineView</div></header><main><section class="movie-section"><h2 class="section-title">✨ New Uploads</h2><div class="movie-grid">{grid_html}</div></section></main><footer><p>&copy; 2025 CineView</p></footer></body></html>"""
    
    push_github("index.html", index_full, "System Refresh: Full AI Poster Grid")

if __name__ == "__main__":
    main()
