import os, requests, base64, json, time, re

# --- CREDENTIALS ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
TMDB_KEY = "dc691868b09daaabe9acc238ed898cf7"
GEMINI_KEY = "" # System provided

# Folders to strictly ignore
BLACKLIST = ["recycle bin", "deleted", "trash", "temp", "hidden", "internal"]

def clean_name_ai(raw):
    """Aggressively scrubs filenames to return only 'Movie Title (Year)'."""
    print(f"   [AI Scrubbing] {raw}...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"Filename: '{raw}'. Extract ONLY the official Movie/Series Title and Release Year. Return as JSON: {{\"t\":\"Title\", \"y\":\"Year\"}}. No noise like 1080p, WEBRip, or .mp4."}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            d = json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'])
            return d.get('t', raw), d.get('y', '')
    except: pass
    return raw, ""

def fetch_tmdb(title, year):
    """Gets official theatrical assets and ratings from TMDB."""
    print(f"   [TMDB Search] {title}")
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={title}&year={year}"
        res = requests.get(url, timeout=10).json()
        if res.get('results'):
            it = res['results'][0]
            p = it.get('poster_path')
            b = it.get('backdrop_path')
            return {
                "poster": f"https://image.tmdb.org/t/p/w500{p}" if p else None,
                "back": f"https://image.tmdb.org/t/p/original{b}" if b else "",
                "score": round(it.get('vote_average', 0), 1),
                "genre": "Premium Cinema"
            }
    except: pass
    return {"poster": f"https://via.placeholder.com/500x750?text={title}", "score": "N/A", "genre": "Cinema", "back": ""}

def push_github(path, content, msg):
    """Forces an update to GitHub by retrieving current SHA."""
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
    print("--- 🚀 STARTING CINEVIEW MOBILE-FIRST DEPLOYMENT ---")
    if not ABYSS_KEY or not GH_TOKEN: return

    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        items = requests.get(url, timeout=30).json().get('items', [])
    except: return

    catalog = []

    for item in items:
        raw, iid, is_dir = item.get('name'), item.get('id'), item.get('isDir', False)
        if not iid or any(x in raw.lower() for x in BLACKLIST): continue
        
        name, year = clean_name_ai(raw)
        data = fetch_tmdb(name, year)
        
        if not is_dir:
            path = f"Insider/{iid}.html"
            catalog.append({"n": name, "y": year, "u": path, "i": data['poster'], "t": "Movie", "s": data['score']})
            # Movie Player UI
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"><title>{name}</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700&display=swap" rel="stylesheet"><style>:root{{--bg:#020205;--acc:#00d2ff;}} body{{background:var(--bg);color:#fff;font-family:'Plus Jakarta Sans',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:15px;box-sizing:border-box;}} .card{{width:100%;max-width:900px;background:#0d0d12;border-radius:28px;overflow:hidden;border:1px solid #1a1a25;box-shadow:0 30px 80px rgba(0,0,0,0.9);}} .v-box{{position:relative;width:100%;aspect-ratio:16/9;}} iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none;}} .meta{{padding:25px;}} .t{{font-size:1.6rem;font-weight:700;color:var(--acc);margin-bottom:10px;}}</style></head><body><div class="card"><div class="v-box"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="meta"><div class="t">{name} ({year})</div><p style="opacity:0.6;font-size:0.9rem;">⭐ {data['score']} Rating | 4K HDR Quality</p></div></div></body></html>"""
            push_github(path, html, f"Elite Sync: {name}")
        else:
            path = f"episodes/{iid}.html"
            catalog.append({"n": name, "y": year, "u": path, "i": data['poster'], "t": "Series", "s": data['score']})
            try:
                f_res = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
                children = f_res.get('items', [])
                ep_js = [{"n": clean_name_ai(c.get('name'))[0], "v": f"https://short.icu/{c.get('id')}"} for c in children]
                opts = "".join([f'<option value="{i}">Episode {i+1}: {e["n"]}</option>' for i,e in enumerate(ep_js)])
                # Series Player UI
                html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{background:#020205;color:#fff;font-family:sans-serif;margin:0;}} .h{{padding:60px 20px;text-align:center;background:linear-gradient(rgba(0,0,0,0.8),#020205),url('{data['back'] or data['poster']}');background-size:cover;}} iframe{{width:100%;aspect-ratio:16/9;border:none;}} .sel{{width:90%;margin:20px auto;display:block;padding:18px;background:#14141c;color:#fff;border-radius:15px;border:1px solid #333;font-size:1rem;appearance:none;outline:none;}}</style></head><body><div class="h"><h1>{name}</h1><p>{len(ep_js)} Episodes Available</p></div><iframe id="ifr" src="" allowfullscreen></iframe><select class="sel" onchange="ch(this.value)">{opts}</select><h2 id="et" style="text-align:center;color:#00d2ff;margin-top:20px;"></h2><script>const eps={json.dumps(ep_js)};function ch(i){{const e=eps[i];document.getElementById('ifr').src=e.v;document.getElementById('et').textContent=e.n;}}ch(0);</script></body></html>"""
                push_github(path, html, f"Elite Sync Series: {name}")
            except: pass

    # --- ULTIMATE HOME PAGE (PREMIUM UX) ---
    grid_items = "".join([f"""
    <a href="{c['u']}" class="m-link" data-title="{c['n'].lower()}">
        <div class="m-card">
            <div class="p-con">
                <img src="{c['i']}" class="p-img" loading="lazy">
                <div class="badge">⭐ {c['s']}</div>
                <div class="type">{c['t']}</div>
            </div>
            <div class="m-info">
                <h3>{c['n']}</h3>
                <p>{c['y'] or '2025'}</p>
            </div>
        </div>
    </a>""" for c in catalog])

    index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0"><title>CineView Hub</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet"><style>
    :root{{--bg:#010103;--card:#0d0d14;--accent:#00d2ff;--glass:rgba(10,10,15,0.85);}}
    body{{background:var(--bg);color:#fff;font-family:'Plus Jakarta Sans',sans-serif;margin:0;}}
    header{{position:fixed;top:0;width:100%;z-index:100;background:var(--glass);backdrop-filter:blur(25px);padding:15px 20px;box-sizing:border-box;border-bottom:1px solid rgba(255,255,255,0.05);display:flex;flex-direction:column;align-items:center;}}
    .logo{{font-size:1.3rem;font-weight:900;color:var(--accent);letter-spacing:2px;margin-bottom:12px;}}
    .s-box{{width:100%;max-width:500px;}}
    input{{width:100%;padding:14px 22px;border-radius:15px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);color:#fff;outline:none;font-size:16px;box-sizing:border-box;transition:0.3s;}}
    input:focus{{border-color:var(--accent);box-shadow:0 0 15px rgba(0,210,255,0.2);}}
    main{{margin-top:145px;padding:15px;}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(165px,1fr));gap:25px;max-width:1400px;margin:auto;}}
    .m-link{{text-decoration:none;}}
    .m-card{{background:var(--card);border-radius:22px;overflow:hidden;border:1px solid #1a1a25;transition:0.3s;height:100%;box-shadow:0 15px 40px rgba(0,0,0,0.5);}}
    .p-con{{position:relative;aspect-ratio:2/3;overflow:hidden;background:#111;}}
    .p-img{{width:100%;height:100%;object-fit:cover;transition:0.6s;}}
    .m-card:hover .p-img{{transform:scale(1.08);}}
    .badge{{position:absolute;top:10px;left:10px;background:rgba(0,0,0,0.6);backdrop-filter:blur(10px);padding:5px 10px;border-radius:10px;font-size:0.7rem;font-weight:bold;color:var(--accent);border:1px solid rgba(0,210,255,0.2);}}
    .type{{position:absolute;bottom:12px;right:12px;background:var(--accent);color:#000;padding:3px 10px;border-radius:8px;font-size:0.65rem;font-weight:900;text-transform:uppercase;}}
    .m-info{{padding:18px;}} h3{{margin:0;font-size:0.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff;}} p{{margin:8px 0 0;font-size:0.8rem;color:#777;}}
    @media(max-width:600px){{.grid{{grid-template-columns:repeat(2,1fr);gap:15px;}} .logo{{font-size:1.1rem;}}}}
    </style></head><body>
    <header><div class="logo">CINEVIEW</div><div class="s-box"><input type="text" id="sb" placeholder="Search premium library..." oninput="sf()"></div></header>
    <main><div class="grid" id="mg">{grid_items}</div></main>
    <script>function sf(){{const v=document.getElementById('sb').value.toLowerCase();document.querySelectorAll('.m-link').forEach(c=>c.style.display=c.dataset.title.includes(v)?'block':'none')}}</script>
    </body></html>"""
    
    push_github("index.html", index_html, "Elite Total UI/UX Deployment")
    print("--- 🏁 TOTAL DEPLOYMENT FINISHED ---")

if __name__ == "__main__":
    main()
