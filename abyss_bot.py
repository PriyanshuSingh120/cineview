import os, requests, base64, json, time, re

# --- CONFIGURATION ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
# The Gemini API Key is provided by the execution environment
GEMINI_KEY = "" 
# Get a free key at omdbapi.com
OMDB_API_KEY = "eb154546" # Example Key; replace if needed

BLACKLIST = ["recycle bin", "deleted", "trash", "temp", "hidden"]

def clean_title_ai(raw_name):
    """Uses AI to extract the clean Movie/Series Title and Year."""
    print(f"   [AI] Cleaning title: {raw_name}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Extract ONLY the official Movie/Series Title and Release Year from this filename: '{raw_name}'. Return as a JSON: {{\"title\": \"...\", \"year\": \"...\"}}. No other text."}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            data = json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'])
            return data.get('title', raw_name), data.get('year', '2025')
    except: pass
    return raw_name, "2025"

def fetch_omdb_data(title, year):
    """Fetches high-quality poster and metadata from OMDB API."""
    print(f"   [OMDB] Fetching data for: {title} ({year})...")
    try:
        url = f"http://www.omdbapi.com/?t={title}&y={year}&apikey={OMDB_API_KEY}"
        res = requests.get(url, timeout=10).json()
        if res.get('Response') == 'True':
            return {
                "poster": res.get('Poster') if res.get('Poster') != 'N/A' else None,
                "genre": res.get('Genre', 'Cinema'),
                "rating": res.get('imdbRating', 'N/A')
            }
    except: pass
    return {"poster": None, "genre": "Cinema", "rating": "N/A"}

def force_push_github(path, content, msg):
    """Pushes/Updates a file on GitHub aggressively."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    payload = {"message": msg, "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')}
    if sha: payload["sha"] = sha
    res = requests.put(url, headers=headers, json=payload)
    print(f"   [GitHub] {path} -> {res.status_code}")
    return res.status_code

def main():
    print("--- 🚀 ELITE CINEVIEW ENGINE ACTIVATED ---")
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing!"); return

    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        items = requests.get(url, timeout=30).json().get('items', [])
    except: return

    catalog = []

    for item in items:
        raw_name, iid, is_dir = item.get('name'), item.get('id'), item.get('isDir', False)
        if not iid or any(word in raw_name.lower() for word in BLACKLIST): continue
        
        # 1. Clean Title with AI
        title, year = clean_title_ai(raw_name)
        
        # 2. Get Metadata with OMDB
        meta = fetch_omdb_data(title, year)
        poster = meta['poster'] if meta['poster'] else f"https://via.placeholder.com/500x750/111/fff?text={title.replace(' ', '+')}"
        
        if not is_dir:
            path = f"Insider/{iid}.html"
            catalog.append({"name": title, "year": year, "url": path, "img": poster, "type": "Movie", "genre": meta['genre']})
            
            # MOVIE PLAYER UI
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{title} ({year})</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700&display=swap" rel="stylesheet"><style>:root{{--bg:#050508;--card:#101016;--accent:#00e5ff;}} body{{background:var(--bg);color:#fff;font-family:'Plus Jakarta Sans',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:15px;box-sizing:border-box;}} .c{{width:100%;max-width:1000px;background:var(--card);border-radius:28px;overflow:hidden;border:1px solid #1a1a25;box-shadow:0 40px 100px rgba(0,0,0,0.8);}} .v{{position:relative;width:100%;aspect-ratio:16/9;}} iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none;}} .m{{padding:30px;}} .t{{font-size:1.8rem;font-weight:700;color:var(--accent);margin-bottom:10px;}} .d{{opacity:0.6;font-size:0.9rem;display:flex;gap:20px;}}</style></head><body><div class="c"><div class="v"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="m"><div class="t">{title} ({year})</div><div class="d"><span>{meta['genre']}</span><span>⭐ {meta['rating']}</span><span>4K Streaming</span></div></div></div></body></html>"""
            force_push_github(path, html, f"Elite Sync Movie: {title}")
            
        else:
            path = f"episodes/{iid}.html"
            catalog.append({"name": title, "year": year, "url": path, "img": poster, "type": "Series", "genre": meta['genre']})
            try:
                f_res = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
                eps = [{"n": clean_title_ai(c.get('name'))[0], "v": f"https://short.icu/{c.get('id')}"} for c in f_res.get('items', [])]
                opts = "".join([f'<option value="{i}">Episode {i+1}: {e["n"]}</option>' for i,e in enumerate(eps)])
                
                # SERIES PLAYER UI (Mobile Friendly)
                html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700&display=swap" rel="stylesheet"><style>body{{background:#050508;color:#fff;font-family:'Plus Jakarta Sans',sans-serif;margin:0;}} .h-sec{{padding:60px 20px;text-align:center;background:linear-gradient(rgba(0,0,0,0.85),#050508),url('{poster}');background-size:cover;}} .v-box{{width:100%;aspect-ratio:16/9;background:#000;}} iframe{{width:100%;height:100%;border:none;}} .controls{{padding:25px;max-width:900px;margin:auto;}} .sel-btn{{width:100%;padding:18px;background:#14141c;color:#fff;border:1px solid #2a2a35;border-radius:15px;font-size:1.1rem;appearance:none;outline:none;cursor:pointer;}}</style></head><body><div class="h-sec"><h1>{title}</h1><p>{len(eps)} Episodes • {meta['genre']}</p></div><div class="v-box"><iframe id="ifr" src="" allowfullscreen></iframe></div><div class="controls"><select class="sel-btn" onchange="ch(this.value)">{opts}</select><h2 id="et" style="color:#00e5ff;margin-top:25px;font-size:1.4rem;"></h2></div><script>const EPS={json.dumps(eps)};function ch(i){{const e=EPS[i];document.getElementById('ifr').src=e.v;document.getElementById('et').textContent=e.n;}}ch(0);</script></body></html>"""
                force_push_github(path, html, f"Elite Sync Series: {title}")
            except: pass

    # --- ELITE HOMEPAGE ---
    grid_html = "".join([f"""
    <a href="{c['url']}" class="movie-link" data-title="{c['name'].lower()}">
        <div class="movie-card">
            <div class="movie-poster-container">
                <img src="{c['img']}" alt="{c['name']}" class="movie-poster" loading="lazy">
                <div class="type-tag">{c['type']}</div>
            </div>
            <div class="movie-info">
                <h3>{c['name']}</h3>
                <p>{c['year']} • {c['genre']}</p>
            </div>
        </div>
    </a>""" for c in catalog])

    index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>🎬 CineView Hub</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet"><style>
    :root{{--bg:#020205;--card:#0a0a0f;--accent:#00d2ff;}}
    body{{background:var(--bg);color:#fff;font-family:'Plus Jakarta Sans',sans-serif;margin:0;}}
    .hero{{padding:120px 20px;text-align:center;background:linear-gradient(rgba(0,0,0,0.7),var(--bg)),url('https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=1600');background-size:cover;}}
    .hero h1{{font-size:3.5rem;font-weight:800;margin:0;letter-spacing:-2px;}}
    .s-box{{max-width:650px;margin:30px auto;position:relative;}}
    #sb{{width:100%;padding:22px 35px;border-radius:50px;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.05);color:#fff;font-size:1.1rem;outline:none;backdrop-filter:blur(20px);transition:0.4s;box-sizing:border-box;}}
    #sb:focus{{border-color:var(--accent);box-shadow:0 0 40px rgba(0,210,255,0.3);}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:35px;padding:40px;max-width:1400px;margin:auto;}}
    .movie-card{{background:var(--card);border-radius:24px;overflow:hidden;border:1px solid #1a1a25;transition:0.5s;height:100%;position:relative;}}
    .movie-poster-container{{aspect-ratio:2/3;position:relative;overflow:hidden;}}
    .movie-poster{{width:100%;height:100%;object-fit:cover;transition:0.8s;}}
    .movie-card:hover{{transform:translateY(-15px);border-color:var(--accent);box-shadow:0 25px 50px rgba(0,0,0,0.6);}}
    .movie-card:hover .movie-poster{{transform:scale(1.1);}}
    .type-tag{{position:absolute;top:15px;right:15px;background:rgba(0,0,0,0.7);padding:6px 14px;border-radius:12px;font-size:0.75rem;font-weight:800;color:var(--accent);border:1px solid var(--accent);backdrop-filter:blur(10px);}}
    .movie-info{{padding:22px;}} .movie-info h3{{font-size:1.1rem;margin:0;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
    .movie-info p{{font-size:0.85rem;color:#888;margin-top:10px;}}
    .movie-link{{text-decoration:none;}}
    @media(max-width:600px){{ .grid{{grid-template-columns:repeat(2,1fr);gap:15px;padding:15px;}} .hero h1{{font-size:2.2rem;}} }}
    </style></head><body>
    <div class="hero"><h1>CINEVIEW</h1><div class="s-box"><input type="text" id="sb" placeholder="Search elite cinema..." oninput="sf()"></div></div>
    <main><section class="grid" id="mg">{grid_html}</section></main>
    <script>function sf(){{const v=document.getElementById('sb').value.toLowerCase();document.querySelectorAll('.movie-link').forEach(c=>c.style.display=c.dataset.title.includes(v)?'block':'none')}}</script>
    </body></html>"""
    
    force_push_github("index.html", index_html, "Elite OMDB Integrated Total Refresh")
    print("--- 🏁 TOTAL SYNC FINISHED ---")

if __name__ == "__main__":
    main()
