import os, requests, base64, json, time, re

# --- CONFIGURATION ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
API_KEY = "" # Provided by environment

BLACKLIST = ["recycle bin", "deleted", "trash", "temp", "hidden"]

def clean_title_ai(raw_name):
    """Uses AI to extract a clean Movie Title and Year from a messy filename."""
    print(f"   [AI] Cleaning title: {raw_name}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Extract ONLY the official Movie/Series Title and Release Year from this filename: '{raw_name}'. Format it as 'Title (Year)'. If no year is found, just return 'Title'. Return nothing else."
                }]
            }]
        }
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            clean = res.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            return clean if clean else raw_name
    except: pass
    return raw_name

def fetch_poster_ai(clean_title):
    """Finds a high-quality vertical theatrical poster."""
    print(f"   [AI Search] Finding poster for: {clean_title}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Official high-resolution vertical theatrical movie poster URL for '{clean_title}'. Return ONLY the raw URL string."}]}],
            "tools": [{"google_search": {}}]
        }
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            poster = res.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            if poster.startswith("http"): return poster
    except: pass
    return f"https://via.placeholder.com/500x750/111/fff?text={clean_title.replace(' ', '+')}"

def force_push_github(path, content, msg):
    """Aggressively forces a file update."""
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
    print("--- 🚀 MOBILE-READY CINEVIEW START ---")
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
        
        # CLEAN THE TITLE
        display_title = clean_title_ai(raw_name)
        poster = fetch_poster_ai(display_title)
        
        if not is_dir:
            path = f"Insider/{iid}.html"
            catalog.append({"name": display_title, "url": path, "img": poster, "type": "Movie"})
            html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{display_title}</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet"><style>body{{background:#050507;color:#fff;font-family:'Inter',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:15px;box-sizing:border-box;}}.c{{width:100%;max-width:900px;background:#111116;border-radius:20px;overflow:hidden;border:1px solid #222;}}.v{{position:relative;padding-bottom:56.25%;}}iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none;}}.m{{padding:20px;}}.t{{font-size:1.4rem;font-weight:700;color:#00d2ff;}}</style></head><body><div class="c"><div class="v"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="m"><div class="t">{display_title}</div><p style="opacity:0.6">4K Ultra HD Streaming</p></div></div></body></html>"""
            force_push_github(path, html, f"Update Movie: {display_title}")
        else:
            path = f"episodes/{iid}.html"
            catalog.append({"name": display_title, "url": path, "img": poster, "type": "Series"})
            try:
                f_res = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
                children = f_res.get('items', [])
                ep_js = [{"n": clean_title_ai(c.get('name')), "v": f"https://short.icu/{c.get('id')}"} for c in children]
                opts = "".join([f'<option value="{i}">EP {i+1}: {e["n"]}</option>' for i,e in enumerate(ep_js)])
                html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>body{{background:#000;color:#fff;font-family:sans-serif;margin:0;}}.p-box{{width:100%;aspect-ratio:16/9;background:#111;}}iframe{{width:100%;height:100%;border:none;}}.controls{{padding:20px;}}.sel{{width:100%;padding:15px;background:#222;color:#fff;border:1px solid #444;border-radius:10px;font-size:1rem;}}</style></head><body><div class="p-box"><iframe id="ifr" src="" allowfullscreen></iframe></div><div class="controls"><h2>{display_title}</h2><select class="sel" onchange="ch(this.value)">{opts}</select><h3 id="et" style="margin-top:20px;color:#00d2ff;"></h3></div><script>const EPS={json.dumps(ep_js)};function ch(i){{const e=EPS[i];document.getElementById('ifr').src=e.v;document.getElementById('et').textContent=e.n;}}ch(0);</script></body></html>"""
                force_push_github(path, html, f"Update Series: {display_title}")
            except: pass

    # 3. PREMIUM MOBILE INDEX
    grid_html = "".join([f'<a href="{c["url"]}" class="movie-link" data-title="{c["name"].lower()}"><div class="movie-card"><div class="movie-poster-container"><img src="{c["img"]}" class="movie-poster" loading="lazy"><div class="type-badge">{c["type"]}</div></div><div class="movie-info"><h3>{c["name"]}</h3></div></div></a>' for c in catalog])
    index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>CineView Hub</title><link rel="stylesheet" href="style.css"><style>
    body{{background:#050507;color:#fff;font-family:sans-serif;margin:0;}}
    .hero{{padding:60px 20px;text-align:center;background:linear-gradient(rgba(0,0,0,0.8),#050507),url('https://images.unsplash.com/photo-1485846234645-a62644f84728?w=1200');background-size:cover;}}
    #sb{{width:90%;max-width:500px;padding:15px 25px;border-radius:30px;border:1px solid #333;background:rgba(255,255,255,0.05);color:#fff;outline:none;backdrop-filter:blur(10px);}}
    .movie-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:20px;padding:20px;}}
    .movie-card{{background:#111;border-radius:15px;overflow:hidden;border:1px solid #222;position:relative;}}
    .movie-poster-container{{aspect-ratio:2/3;overflow:hidden;}}
    .movie-poster{{width:100%;height:100%;object-fit:cover;}}
    .type-badge{{position:absolute;top:10px;right:10px;background:#000;color:#00d2ff;padding:3px 8px;font-size:0.7rem;border-radius:5px;border:1px solid #00d2ff;}}
    .movie-info{{padding:12px;}} .movie-info h3{{font-size:0.9rem;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
    .movie-link{{text-decoration:none;}}
    @media(max-width:600px){{.movie-grid{{grid-template-columns:repeat(2,1fr);gap:12px;}}}}
    </style></head><body>
    <div class="hero"><h1>CINEVIEW</h1><input type="text" id="sb" placeholder="Search..." oninput="sf()"></div>
    <div class="movie-grid">{grid_html}</div>
    <script>function sf(){{const v=document.getElementById('sb').value.toLowerCase();document.querySelectorAll('.movie-link').forEach(c=>c.style.display=c.dataset.title.includes(v)?'block':'none')}}</script>
    </body></html>"""
    
    force_push_github("index.html", index_html, "Ultimate Mobile & Title Cleanup Refresh")
    print("--- 🏁 TOTAL SYNC FINISHED ---")

if __name__ == "__main__":
    main()
