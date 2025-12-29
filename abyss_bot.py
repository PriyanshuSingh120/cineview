import os, requests, json, time, re

# --- CONFIGURATION ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_REPO = os.getenv("GITHUB_REPOSITORY")
TMDB_KEY = "dc691868b09daaabe9acc238ed898cf7"

# Custom AI Endpoint
API_URL = os.getenv("CUSTOM_API_URL") 
API_KEY = os.getenv("CUSTOM_API_KEY")

BLACKLIST = ["recycle bin", "deleted", "trash", "temp", "hidden", "internal"]

def get_existing_ids():
    """Checks local folders for existing files to skip them."""
    existing = set()
    for folder in ["Insider", "episodes"]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                if file.endswith(".html"):
                    existing.add(file.replace(".html", ""))
    return existing

def clean_title_ai(raw):
    """Uses custom AI to scrub messy filenames into clean titles."""
    if not API_KEY or not API_URL:
        return raw, ""
    try:
        clean_raw = re.sub(r'\.(mp4|mkv|avi|mov|ts)$', '', raw, flags=re.I)
        payload = {
            "contents": [{"parts": [{"text": f"Scrub this filename: '{clean_raw}'. Return ONLY a JSON object with 't' (Clean Title) and 'y' (Year). Remove all quality tags and junk."}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        res = requests.post(f"{API_URL}?key={API_KEY}", json=payload, timeout=20)
        if res.status_code == 200:
            d = json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'])
            return d.get('t', raw), d.get('y', '')
    except: pass
    return raw, ""

def fetch_tmdb(title, year):
    """Fetches high-quality theatrical posters from TMDB."""
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
                "score": round(it.get('vote_average', 0), 1)
            }
    except: pass
    return {"poster": f"https://via.placeholder.com/500x750?text={title}", "score": "N/A", "back": ""}

def save_file(path, content):
    """Fixed: Saves content to disk, handling root files correctly."""
    directory = os.path.dirname(path)
    if directory: # Only create directory if path is not in root
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def natural_sort_key(s):
    """Sorting logic to ensure Episode 1 comes before Episode 10."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def main():
    print("--- 🎬 CINEVIEW ELITE SYNC START ---")
    if not ABYSS_KEY:
        print("Error: ABYSS_KEY is missing!"); return

    existing_ids = get_existing_ids()
    print(f"Skipping {len(existing_ids)} already synced files...")

    try:
        items = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100").json().get('items', [])
    except Exception as e:
        print(f"Abyss API Error: {e}"); return

    catalog = []

    for item in items:
        raw, iid, is_dir = item.get('name'), item.get('id'), item.get('isDir', False)
        if not iid or any(x in raw.lower() for x in BLACKLIST): continue
        
        name, year = clean_title_ai(raw)
        data = fetch_tmdb(name, year)
        path = f"Insider/{iid}.html" if not is_dir else f"episodes/{iid}.html"
        
        catalog.append({"n": name, "y": year, "u": path, "i": data['poster'], "t": "Movie" if not is_dir else "Series", "s": data['score']})

        if iid in existing_ids: continue
        
        if not is_dir:
            # MOVIE PLAYER
            html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700&display=swap" rel="stylesheet"><style>body{{background:#020205;color:#fff;font-family:'Plus Jakarta Sans',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:15px;box-sizing:border-box;}}.c{{width:100%;max-width:900px;background:#0d0d12;border-radius:24px;border:1px solid #1a1a25;box-shadow:0 30px 80px rgba(0,0,0,0.9);overflow:hidden;}}.v{{position:relative;width:100%;aspect-ratio:16/9;}}iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none;}}.m{{padding:25px;}}.t{{font-size:1.6rem;font-weight:700;color:#00d2ff;margin:0 0 10px;}}</style></head><body><div class="c"><div class="v"><iframe src="https://short.icu/{iid}" allowfullscreen></iframe></div><div class="m"><h1 class="t">{name} ({year})</h1><p style="opacity:0.6">⭐ {data['score']} Rating</p></div></div></body></html>"""
            save_file(path, html)
            print(f"   [New Movie] {name}")
        else:
            # SERIES PLAYER
            try:
                f_res = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}").json()
                e_items = f_res.get('items', [])
                e_items.sort(key=lambda x: natural_sort_key(x.get('name', '')))
                
                ep_js = []
                opts = ""
                for idx, c in enumerate(e_items):
                    en, _ = clean_title_ai(c.get('name'))
                    ep_js.append({"n": en, "v": f"https://short.icu/{c.get('id')}"})
                    opts += f'<option value="{idx}">Episode {idx+1}: {en}</option>'
                
                html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{background:#020205;color:#fff;font-family:sans-serif;margin:0;}}iframe{{width:100%;aspect-ratio:16/9;border:none;}}.s{{width:92%;margin:20px auto;display:block;padding:18px;background:#111;color:#fff;border-radius:15px;border:1px solid #333;font-size:1rem;appearance:none;outline:none;}}</style></head><body><div style="padding:60px 20px;text-align:center;background:linear-gradient(rgba(0,0,0,0.8),#020205),url('{data['back'] or data['poster']}');background-size:cover;"><h1>{name}</h1></div><iframe id="p" src="" allowfullscreen></iframe><select class="s" onchange="ch(this.value)">{opts}</select><h2 id="et" style="text-align:center;color:#00d2ff;margin-top:15px;"></h2><script>const eps={json.dumps(ep_js)};function ch(i){{const e=eps[i];document.getElementById('p').src=e.v;document.getElementById('et').textContent=e.n;}}ch(0);</script></body></html>"""
                save_file(path, html)
                print(f"   [New Series] {name}")
            except: pass

    # --- ELITE INDEX ---
    grid_html = "".join([f"""
    <a href="{c['u']}" class="m-link" data-title="{c['n'].lower()}">
        <div class="m-card">
            <div class="p-con"><img src="{c['i']}" class="p-img" loading="lazy"><div class="badge">⭐ {c['s']}</div><div class="type-tag">{c['t']}</div></div>
            <div class="m-info"><h3>{c['n']}</h3><p>{c['y'] or '2025'}</p></div>
        </div>
    </a>""" for c in catalog])

    index_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0"><title>🎬 CineView Hub</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet"><style>
    :root{{--bg:#010103;--card:#0d0d14;--accent:#00d2ff;--glass:rgba(10,10,15,0.85);}}
    body{{background:var(--bg);color:#fff;font-family:'Plus Jakarta Sans',sans-serif;margin:0;}}
    header{{position:fixed;top:0;width:100%;z-index:100;background:var(--glass);backdrop-filter:blur(25px);padding:15px;box-sizing:border-box;border-bottom:1px solid #222;display:flex;flex-direction:column;align-items:center;}}
    .logo{{font-size:1.3rem;font-weight:900;color:var(--accent);letter-spacing:2px;margin-bottom:10px;text-shadow:0 0 10px rgba(0,210,255,0.5);}}
    .s-box{{width:100%;max-width:500px;}}
    input{{width:100%;padding:14px 22px;border-radius:15px;border:1px solid #333;background:rgba(255,255,255,0.05);color:#fff;outline:none;font-size:16px;box-sizing:border-box;}}
    main{{margin-top:140px;padding:15px;}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px, 1fr));gap:15px;max-width:1400px;margin:auto;}}
    .m-card{{background:var(--card);border-radius:18px;overflow:hidden;border:1px solid #1a1a25;transition:0.3s;height:100%;display:flex;flex-direction:column;}}
    .p-con{{position:relative;width:100%;aspect-ratio:2/3;overflow:hidden;}}
    .p-img{{width:100%;height:100%;object-fit:cover;}}
    .badge{{position:absolute;top:8px;left:8px;background:rgba(0,0,0,0.6);backdrop-filter:blur(8px);padding:4px 8px;border-radius:8px;font-size:0.6rem;font-weight:bold;color:var(--accent);border:1px solid rgba(0,210,255,0.2);}}
    .type-tag{{position:absolute;bottom:10px;right:10px;background:var(--accent);color:#000;padding:2px 8px;border-radius:6px;font-size:0.55rem;font-weight:900;text-transform:uppercase;}}
    .m-info{{padding:12px;flex-grow:1;min-width:0;}} h3{{margin:0;font-size:0.85rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff;}} p{{margin:5px 0 0;font-size:0.75rem;color:#777;}}
    .m-link{{text-decoration:none;}}
    @media(max-width:600px){{.grid{{grid-template-columns:repeat(2,1fr);gap:12px;}}}}
    </style></head><body>
    <header><div class="logo">CINEVIEW</div><div class="s-box"><input type="text" id="sb" placeholder="Search library..." oninput="sf()"></div></header>
    <main><div class="grid" id="mg">{grid_html}</div></main>
    <script>function sf(){{const v=sb.value.toLowerCase();document.querySelectorAll('.m-link').forEach(c=>c.style.display=c.dataset.title.includes(v)?'block':'none')}}</script>
    </body></html>"""
    
    save_file("index.html", index_html)
    print("--- 🏁 SYNC FINISHED (FILES SAVED LOCALLY) ---")

if __name__ == "__main__":
    main()
