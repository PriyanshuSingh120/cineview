import os, requests, base64, json, time, re

# --- CREDENTIALS ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
TMDB_KEY = "dc691868b09daaabe9acc238ed898cf7"
GEMINI_KEY = "" # Provided by environment

BLACKLIST = ["recycle bin", "deleted", "trash", "temp", "hidden"]

def get_synced_files():
    """Returns a list of all HTML files already in the repo to skip them."""
    synced = []
    headers = {"Authorization": f"token {GH_TOKEN}"}
    for folder in ["Insider", "episodes"]:
        url = f"https://api.github.com/repos/{GH_REPO}/contents/{folder}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            synced.extend([f['name'].replace('.html', '') for f in r.json() if f['name'].endswith('.html')])
    return synced

def clean_title_ai(raw):
    """Uses Gemini to extract the professional title and year."""
    print(f"   [AI] Scrubbing: {raw}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Extract ONLY the official Title and Year from this filename: '{raw}'. Return as JSON: {{\"t\":\"Title\", \"y\":\"Year\"}}. No noise."}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            d = json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'])
            return d.get('t', raw), d.get('y', '')
    except: pass
    return raw, ""

def fetch_tmdb(title, year):
    """Fetches high-res posters and metadata from TMDB."""
    print(f"   [TMDB] Researching: {title}")
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={title}&year={year}"
        res = requests.get(url, timeout=10).json()
        if res.get('results'):
            it = res['results'][0]
            path = it.get('poster_path')
            back = it.get('backdrop_path')
            return {
                "poster": f"https://image.tmdb.org/t/p/w500{path}" if path else None,
                "backdrop": f"https://image.tmdb.org/t/p/original{back}" if back else "",
                "score": round(it.get('vote_average', 0), 1)
            }
    except: pass
    return {"poster": f"https://via.placeholder.com/500x750?text={title}", "score": "N/A", "backdrop": ""}

def push_github(path, content, msg):
    """Pushes file to GitHub."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    payload = {"message": msg, "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')}
    if sha: payload["sha"] = sha
    res = requests.put(url, headers=headers, json=payload)
    print(f"   [GitHub] {path} -> {res.status_code}")

def main():
    print("--- 🎬 CINEVIEW ELITE ENGINE START ---")
    if not ABYSS_KEY or not GH_TOKEN: return

    # 1. Get synced files
    synced_ids = get_synced_files()

    # 2. Fetch Abyss Items
    try:
        items = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100").json().get('items', [])
    except: return

    catalog = []

    for item in items:
        raw, iid, is_dir = item.get('name'), item.get('id'), item.get('isDir', False)
        if not iid or any(x in raw.lower() for x in BLACKLIST): continue
        
        name, year = clean_title_ai(raw)
        data = fetch_tmdb(name, year)
        path = f"Insider/{iid}.html" if not is_dir else f"episodes/{iid}.html"
        catalog.append({"n": name, "y": year, "u": path, "i": data['poster'], "t": "Movie" if not is_dir else "Series", "s": data['score']})

        # SKIP IF EXISTS
        if iid in synced_ids: continue
        
        if not is_dir:
            # MOVIE PAGE
            html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700&display=swap" rel="stylesheet"><style>body{{background:#020205;color:#fff;font-family:'Plus Jakarta Sans',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:15px;}}.c{{width:100%;max-width:900px;background:#111;border-radius:24px;overflow:hidden;border:1px solid #222;}}.v{{position:relative;width:100%;aspect-ratio:16/9;}}iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none;}}.m{{padding:25px;}}.t{{font-size:1.6rem;font-weight:700;color:#00e5ff;}}</style></head><body><div class="c"><div class="v"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="m"><div class="t">{name} ({year})</div><p style="opacity:0.6">⭐ {data['score']} Rating</p></div></div></body></html>"""
            push_github(path, html, f"Sync Movie: {name}")
        else:
            # SERIES PAGE (WITH SORTED EPISODES)
            try:
                f_res = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
                ep_items = f_res.get('items', [])
                # SORTING: Ensure Ep 1 is first
                ep_items.sort(key=lambda x: x.get('name', '').lower())
                
                ep_js = []
                opts = ""
                for idx, c in enumerate(ep_items):
                    ep_name, _ = clean_title_ai(c.get('name'))
                    ep_js.append({"n": ep_name, "v": f"https://short.icu/{c.get('id')}"})
                    opts += f'<option value="{idx}">Episode {idx+1}: {ep_name}</option>'
                
                html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{background:#020205;color:#fff;font-family:sans-serif;margin:0;}}.h{{padding:60px 20px;text-align:center;background:linear-gradient(rgba(0,0,0,0.8),#020205),url('{data['backdrop'] or data['poster']}');background-size:cover;}}iframe{{width:100%;aspect-ratio:16/9;border:none;}}.s{{width:90%;max-width:500px;margin:20px auto;display:block;padding:18px;background:#111;color:#fff;border-radius:15px;border:1px solid #333;font-size:1rem;appearance:none;}}</style></head><body><div class="h"><h1>{name}</h1></div><iframe id="ifr" src="" allowfullscreen></iframe><select class="s" onchange="ch(this.value)">{opts}</select><h2 id="et" style="text-align:center;color:#00d2ff;"></h2><script>const eps={json.dumps(ep_js)};function ch(i){{const e=eps[i];document.getElementById('ifr').src=e.v;document.getElementById('et').textContent=e.n;}}ch(0);</script></body></html>"""
                push_github(path, html, f"Sync Series: {name}")
            except: pass

    # 3. --- ELITE INDEX (REBUILD) ---
    grid_items = "".join([f"""
    <a href="{c['u']}" class="m-link" data-title="{c['n'].lower()}">
        <div class="m-card">
            <div class="p-con">
                <img src="{c['i']}" class="p-img" loading="lazy">
                <div class="badge">⭐ {c['s']}</div>
            </div>
            <div class="m-info">
                <h3>{c['n']}</h3>
                <p>{c['y'] or '2025'}</p>
            </div>
        </div>
    </a>""" for c in catalog])

    index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"><title>🎬 CineView Hub</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet"><style>
    :root{{--bg:#010103;--card:#0d0d14;--accent:#00d2ff;--glass:rgba(10,10,15,0.85);}}
    body{{background:var(--bg);color:#fff;font-family:'Plus Jakarta Sans',sans-serif;margin:0;}}
    header{{position:fixed;top:0;width:100%;z-index:100;background:var(--glass);backdrop-filter:blur(25px);padding:15px 20px;box-sizing:border-box;border-bottom:1px solid #222;display:flex;flex-direction:column;align-items:center;}}
    .logo{{font-size:1.4rem;font-weight:900;color:var(--accent);letter-spacing:2px;margin-bottom:10px;}}
    .s-box{{width:100%;max-width:500px;}}
    input{{width:100%;padding:14px 22px;border-radius:15px;border:1px solid #333;background:rgba(255,255,255,0.05);color:#fff;outline:none;font-size:16px;box-sizing:border-box;}}
    main{{margin-top:140px;padding:15px;}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:20px;max-width:1400px;margin:auto;}}
    .m-link{{text-decoration:none;}}
    .m-card{{background:var(--card);border-radius:20px;overflow:hidden;border:1px solid #1a1a25;transition:0.3s;height:100%;}}
    .p-con{{position:relative;width:100%;aspect-ratio:2/3;overflow:hidden;}}
    .p-img{{width:100%;height:100%;object-fit:cover;transition:0.6s;}}
    .m-card:hover .p-img{{transform:scale(1.08);}}
    .badge{{position:absolute;top:10px;left:10px;background:rgba(0,0,0,0.6);backdrop-filter:blur(10px);padding:5px 10px;border-radius:10px;font-size:0.7rem;font-weight:bold;color:var(--accent);border:1px solid rgba(0,210,255,0.2);}}
    .m-info{{padding:15px;}} h3{{margin:0;font-size:0.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff;}} p{{margin:8px 0 0;font-size:0.8rem;color:#777;}}
    @media(max-width:600px){{.grid{{grid-template-columns:repeat(2,1fr);gap:12px;}}}}
    </style></head><body>
    <header><div class="logo">CINEVIEW</div><div class="s-box"><input type="text" id="sb" placeholder="Search elite library..." oninput="sf()"></div></header>
    <main><div class="grid" id="mg">{grid_items}</div></main>
    <script>function sf(){{const v=document.getElementById('sb').value.toLowerCase();document.querySelectorAll('.m-link').forEach(c=>c.style.display=c.dataset.title.includes(v)?'block':'none')}}</script>
    </body></html>"""
    
    push_github("index.html", index_html, "Elite Total UI Refresh")
    print("--- 🏁 TOTAL DEPLOYMENT FINISHED ---")

if __name__ == "__main__":
    main()
