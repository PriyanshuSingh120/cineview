import os, requests, base64, json, time

# --- CONFIGURATION ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
# Gemini API Key for Poster Research
GEMINI_KEY = "" 

def fetch_poster_ai(title):
    """Researches the official theatrical poster for a title."""
    print(f"   [AI] Researching poster for: {title}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Find a high-quality direct image URL for the official movie poster of '{title}'. Return ONLY the raw URL string."}]}],
            "tools": [{"google_search": {}}]
        }
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            poster = res.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            if poster.startswith("http"): return poster
    except: pass
    return "https://via.placeholder.com/500x750?text=CineView+Hub"

def push_github(path, content, msg):
    """Pushes/Updates file on GitHub with SHA handling."""
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
    print("--- 🚀 CINEVIEW ULTIMATE ENGINE START ---")
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing!"); return

    # 1. Fetch Abyss Resources
    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        resp = requests.get(url, timeout=30)
        items = resp.json().get('items', [])
        print(f"Total Abyss Resources: {len(items)}")
    except Exception as e:
        print(f"Abyss API Error: {e}"); return

    catalog = []

    # 2. Process Items
    for item in items:
        name, iid, is_dir = item.get('name'), item.get('id'), item.get('isDir', False)
        if not iid: continue
        
        poster = fetch_poster_ai(name)
        
        if not is_dir:
            # --- MOVIE PLAYER (ULTIMATE UI) ---
            path = f"Insider/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Movie"})
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{name} - CineView</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{margin:0;background:#08080c;color:#fff;font-family:'Poppins',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px;}}.container{{width:100%;max-width:1000px;background:#121218;border-radius:24px;overflow:hidden;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5);border:1px solid #222;}}.player-box{{position:relative;padding-bottom:56.25%;}}iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none;}}.info{{padding:30px;}}.title{{font-size:1.8rem;font-weight:700;margin-bottom:10px;color:#00e5ff;}}.meta{{display:flex;gap:20px;font-size:0.9rem;opacity:0.6;}}</style></head><body><div class="container"><div class="player-box"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="info"><div class="title">{name}</div><div class="meta"><span>4K Ultra HD</span><span>2025</span><span>English</span></div></div></div></body></html>"""
            push_github(path, html, f"Sync Movie: {name}")
        
        else:
            # --- SERIES PLAYER (ULTIMATE UI) ---
            path = f"episodes/{iid}.html"
            catalog.append({"name": name, "url": path, "img": poster, "type": "Series"})
            f_resp = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
            children = f_resp.get('items', [])
            ep_js = [{"n": c.get('name'), "u": f"https://short.icu/{c.get('id')}"} for c in children]
            
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{name} - CineView</title><style>body{{background:#08080c;color:#fff;font-family:sans-serif;padding:20px;}}.player-wrapper{{max-width:1000px;margin:auto;background:#111;border-radius:20px;overflow:hidden;}}iframe{{width:100%;aspect-ratio:16/9;border:none;}}.controls{{padding:20px;display:flex;justify-content:space-between;align-items:center;}}select{{background:#222;color:#fff;padding:10px;border-radius:8px;border:1px solid #444;}}</style></head><body><div class="player-wrapper"><iframe></iframe><div class="controls"><div><h2 id="et">{name}</h2><p id="en"></p></div><select id="es" onchange="ch(this.value)"></select></div></div><script>const eps = {json.dumps(ep_js)}; const s = document.getElementById('es'); eps.forEach((e,i)=>{{let o=document.createElement('option');o.value=i;o.textContent=`E${{i+1}}: ${{e.n}}`;s.appendChild(o)}}); function ch(i){{const e=eps[i];document.querySelector('iframe').src=e.u;document.getElementById('en').textContent=`Episode ${{parseInt(i)+1}} of ${{eps.length}}`;}} ch(0);</script></body></html>"""
            push_github(path, html, f"Sync Series: {name}")

    # 3. --- MAIN PAGE (PREMIUM INDEX) ---
    print("Building Ultimate Homepage...")
    grid = "".join([f'<a href="{c["url"]}" class="m-link" data-title="{c["name"].lower()}"><div class="m-card"><img src="{c["img"]}" loading="lazy"><div class="m-info"><h3>{c["name"]}</h3><p>{c["type"]}</p></div></div></a>' for c in catalog])
    
    index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>🎬 CineView Hub</title><style>
    :root{{--bg:#050507;--accent:#00d2ff;--card:#111116;}}
    body{{background:var(--bg);color:#fff;font-family:'Segoe UI',sans-serif;margin:0;}}
    .header{{padding:40px 20px;text-align:center;background:linear-gradient(rgba(0,0,0,0),var(--bg)),url('https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1200&q=80');background-size:cover;}}
    .search-container{{max-width:600px;margin:20px auto;position:relative;}}
    input{{width:100%;padding:15px 25px;border-radius:30px;border:none;background:rgba(255,255,255,0.1);color:#fff;backdrop-filter:blur(10px);font-size:1.1rem;box-sizing:border-box;outline:none;border:1px solid rgba(255,255,255,0.2);}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:25px;padding:40px;max-width:1200px;margin:auto;}}
    .m-link{{text-decoration:none;color:#fff;transition:0.3s;}}
    .m-card{{background:var(--card);border-radius:15px;overflow:hidden;border:1px solid #222;height:100%;}}
    .m-card img{{width:100%;aspect-ratio:2/3;object-fit:cover;}}
    .m-info{{padding:15px;}}
    .m-card:hover{{transform:translateY(-10px);border-color:var(--accent);box-shadow:0 10px 30px rgba(0,210,255,0.2);}}
    </style></head><body>
    <div class="header"><h1>CINEVIEW</h1><div class="search-container"><input type="text" id="srch" placeholder="Search movies or series..." oninput="filter()"></div></div>
    <div class="grid" id="g">{grid}</div>
    <script>function filter(){{const v=document.getElementById('srch').value.lower();document.querySelectorAll('.m-link').forEach(l=>{{l.style.display=l.getAttribute('data-title').includes(v)?'block':'none'}})}}</script>
    </body></html>"""
    
    push_github("index.html", index_html, f"System: Ultimate Refresh ({len(catalog)} items)")
    print("--- 🏁 SYNC FINISHED ---")

if __name__ == "__main__":
    main()
