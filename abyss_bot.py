import os, requests, base64, json, time

# --- CONFIG ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
API_KEY = "" # The environment provides the key automatically

def get_github_file(path):
    """Retrieves content and SHA of a file from GitHub."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data['content']).decode('utf-8')
        return content, data['sha']
    return None, None

def fetch_poster_ai(title, cache):
    """Uses AI to find high-res posters. Checks cache first."""
    if title in cache: return cache[title]
    print(f"   [AI] Finding poster for: {title}")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Direct image URL for official movie poster of '{title}'. Return ONLY the URL."}]}],
            "tools": [{"google_search": {}}]
        }
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            poster = res.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            if poster.startswith("http"):
                cache[title] = poster
                return poster
    except: pass
    return "https://via.placeholder.com/500x750?text=CineView"

def push_github(path, content, msg, sha=None):
    """Pushes/Updates file on GitHub."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"message": msg, "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')}
    if sha: payload["sha"] = sha
    res = requests.put(url, headers=headers, json=payload)
    print(f"   [GitHub] {path} -> {res.status_code}")
    return res.status_code

def main():
    print("--- 🛠️ CINEVIEW ULTIMATE REPAIR START ---")
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing!"); return

    # 1. Load Poster Cache
    p_content, p_sha = get_github_file("posters.json")
    cache = json.loads(p_content) if p_content else {}

    # 2. Get existing files to avoid re-uploading
    synced_ids = set()
    for folder in ["Insider", "episodes"]:
        r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{folder}", headers={"Authorization": f"token {GH_TOKEN}"})
        if r.status_code == 200:
            synced_ids.update([f['name'].replace('.html', '') for f in r.json()])

    # 3. Fetch Abyss Data
    try:
        resp = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100")
        items = resp.json().get('items', [])
        print(f"Abyss items found: {len(items)}")
    except: return

    catalog = []
    has_updates = False

    for item in items:
        name, iid, is_dir = item.get('name'), item.get('id'), item.get('isDir', False)
        if not iid: continue
        
        poster = fetch_poster_ai(name, cache)
        # Use existing paths or new ones
        path = f"Insider/{iid}.html" if not is_dir else f"episodes/{iid}.html"
        catalog.append({"name": name, "url": path, "img": poster, "type": "Movie" if not is_dir else "Series"})

        # SKIP IF ALREADY UPLOADED
        if iid in synced_ids: continue
        
        has_updates = True
        if not is_dir:
            # MOVIE TEMPLATE (Professional Cyan)
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{name}</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet"><style>:root {{ --bg: #0a0a0c; --card: #141418; --accent: #00bcd4; }} body {{ background: var(--bg); color: #fff; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }} .v-card {{ width: 100%; max-width: 900px; background: var(--card); border-radius: 20px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.8); border: 1px solid #222; }} iframe {{ width: 100%; aspect-ratio: 16/9; border: none; }} .meta {{ padding: 25px; }} .t {{ font-size: 1.6rem; font-weight: 700; color: var(--accent); }}</style></head><body><div class="v-card"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe><div class="meta"><div class="t">{name}</div><p>4K Ultra HD • CineView Stream</p></div></div></body></html>"""
        else:
            # SERIES TEMPLATE (Episode Selector)
            f_res = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
            eps = [{"n": c.get('name'), "v": f"https://short.icu/{c.get('id')}"} for c in f_res.get('items', [])]
            opts = "".join([f'<option value="{i}">E{i+1}: {c.get("n")}</option>' for i, c in enumerate(eps)])
            html = f"""<!DOCTYPE html><html><body style="background:#08080a;color:#fff;font-family:sans-serif;"><div style="max-width:1000px;margin:auto;padding:20px;"><h1>{name}</h1><iframe id="ifr" style="width:100%;aspect-ratio:16/9;border-radius:15px;border:1px solid #333;" allowfullscreen></iframe><div style="padding:20px;text-align:right;"><select onchange="document.getElementById('ifr').src=eps[this.value].v" style="padding:10px;background:#222;color:#fff;border-radius:8px;">{opts}</select></div></div><script>const eps={json.dumps(eps)};document.getElementById('ifr').src=eps[0].v;</script></body></html>"""
        
        push_github(path, html, f"New Upload: {name}")

    # 4. Save Cache
    if has_updates:
        push_github("posters.json", json.dumps(cache, indent=2), "Update Cache", p_sha)

    # 5. --- REPAIR HOMEPAGE ---
    grid = "".join([f'<a href="{c["url"]}" class="movie-link" data-title="{c["name"].lower()}"><div class="movie-card"><div class="movie-poster-container"><img src="{c["img"]}" class="movie-poster" loading="lazy"></div><div class="movie-info"><h3>{c["name"]}</h3><p>{c["type"]} | 2025</p></div></div></a>' for c in catalog])
    
    index_html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width,initial-scale=1.0">
        <title>🎬 CineView - Premium Hub</title>
        <link rel="stylesheet" href="style.css">
        <style>
            .hero {{ background: linear-gradient(rgba(0,0,0,0.7), #0a0a0c), url('https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1200'); background-size:cover; padding:100px 20px; text-align:center; }}
            .search-box {{ max-width:600px; margin:auto; position:relative; }}
            input {{ width:100%; padding:18px 30px; border-radius:40px; border:1px solid rgba(255,255,255,0.2); background:rgba(255,255,255,0.1); backdrop-filter:blur(15px); color:#fff; font-size:1.1rem; outline:none; transition:0.3s; }}
            input:focus {{ border-color:#00bcd4; box-shadow: 0 0 15px rgba(0,188,212,0.3); }}
        </style>
    </head>
    <body>
        <header class="main-header"><div class="logo">CineView</div></header>
        <div class="hero">
            <h1>Discover Premium Cinema</h1>
            <div class="search-box">
                <input type="text" id="sb" oninput="sf()" placeholder="Search movies or series...">
            </div>
        </div>
        <main><section class="movie-section"><h2 class="section-title">✨ New Releases</h2><div class="movie-grid" id="mg">{grid}</div></section></main>
        <script>
            function sf() {{
                const v = document.getElementById('sb').value.toLowerCase();
                const cards = document.querySelectorAll('.movie-link');
                cards.forEach(c => c.style.display = c.dataset.title.includes(v) ? "block" : "none");
            }}
        </script>
    </body>
    </html>"""
    
    _, idx_sha = get_github_file("index.html")
    push_github("index.html", index_html, "Force UI Refresh", idx_sha)
    print("--- 🏁 REPAIR COMPLETE ---")

if __name__ == "__main__":
    main()
