import os, requests, base64, json, time

# Config
ABYSS_API_KEY = os.getenv("ABYSS_KEY")
GITHUB_TOKEN = os.getenv("GH_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")

def push(path, content, msg):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    payload = {"message": msg, "content": base64.b64encode(content.encode()).decode()}
    if sha: payload["sha"] = sha
    res = requests.put(url, headers=headers, json=payload)
    print(f"[{res.status_code}] {path}")
    return res.status_code

def main():
    print("Starting Sync...")
    try:
        r = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_API_KEY}&maxResults=100")
        items = r.json().get('items', [])
    except:
        print("API Connection Failed")
        return

    catalog = []

    for item in items:
        name, iid, itype = item['name'], item['id'], item['type']
        
        if itype == 'file':
            # --- Movie Layout ---
            html = f"""<!DOCTYPE html><html><head><title>{name}</title><style>body{{background:#1a1a2e;color:#e4e4e4;font-family:sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}}.video-player-container{{width:90%;max-width:800px;border-radius:12px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,0.5),0 0 15px rgba(100,100,255,0.5);background:#0f0f1d;border:1px solid #3c3c54}}.video-frame-area{{position:relative;width:100%;padding-bottom:56.25%}}iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none}}.player-graphics-area{{padding:20px;background:linear-gradient(135deg,#1f1f3a 0%,#0f0f1d 100%)}}.player-title{{font-size:1.8em;font-weight:bold;color:#a0a0ff}}</style></head><body><div class="video-player-container"><div class="video-frame-area"><iframe src="https://abyss.to/e/{iid}" allowfullscreen></iframe></div><div class="player-graphics-area"><div class="player-title">🎬 {name}</div></div></div></body></html>"""
            push(f"watch/{iid}.html", html, f"Movie: {name}")
            catalog.append({"name": name, "link": f"watch/{iid}.html", "type": "Movie"})
        
        elif itype == 'folder':
            # --- Series Layout ---
            f_r = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_API_KEY}&parentId={iid}")
            eps = [{"name": e['name'], "id": e['id']} for e in f_r.json().get('items', [])]
            if eps:
                ep_js = json.dumps(eps)
                opts = "".join([f'<option value="{i}">E{i+1}</option>' for i in range(len(eps))])
                html = f"""<!DOCTYPE html><html><head><title>{name}</title><style>body{{background:#111;color:#fff;font-family:sans-serif;margin:0}}.banner{{background:#1a1a2e;padding:20px;text-align:center}}#player{{width:100%;aspect-ratio:16/9;background:#000;border:none}}select{{width:100%;padding:15px;background:#333;color:#fff;border:none}}</style></head><body><div class="banner"><h1>{name}</h1></div><iframe id="player" src="" allowfullscreen></iframe><select onchange="change(this.value)">{opts}</select><script>const E={ep_js};function change(i){{document.getElementById('player').src="https://abyss.to/e/"+E[i].id}}window.onload=()=>change(0);</script></body></html>"""
                push(f"series/{iid}.html", html, f"Series: {name}")
                catalog.append({"name": name, "link": f"series/{iid}.html", "type": "Series"})
        
        time.sleep(1.5)

    # --- Home Page Index ---
    cards = "".join([f'<a href="{c["link"]}" style="display:block;padding:20px;margin-bottom:10px;background:#1a1a2e;color:#a0a0ff;text-decoration:none;border-radius:10px;border:1px solid #333"><b>{c["name"]}</b> ({c["type"]})</a>' for c in catalog])
    index_html = f"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1.0'><title>CineView</title></head><body style='background:#0f0f1d;color:#fff;font-family:sans-serif;padding:20px'><h1 style='text-align:center;color:#a0a0ff'>CINEVIEW</h1>{cards}</body></html>"
    push("index.html", index_html, "Update Home")

if __name__ == "__main__":
    main()    return f"""<!DOCTYPE html><html><head><title>{name}</title><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>body{{background:#111;color:#fff;font-family:sans-serif;margin:0}}.player-box{{width:100%;aspect-ratio:16/9;background:#000}}iframe{{width:100%;height:100%;border:none}}.info{{padding:20px}}select{{width:100%;padding:10px;background:#333;color:#fff;border:1px solid #555}}</style></head><body><div class="player-box"><iframe id="ep-frame" src="" allowfullscreen></iframe></div><div class="info"><h1>{name}</h1><select onchange="play(this.value)">{options}</select></div><script>const eps={ep_js};function play(i){{document.getElementById('ep-frame').src="https://abyss.to/e/"+eps[i].id}}window.onload=()=>play(0);</script></body></html>"""

def main():
    print("Connecting to Abyss...")
    resp = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_API_KEY}&maxResults=100")
    items = resp.json().get('items', [])
    
    sync_data = []
    
    for item in items:
        name, iid, itype = item['name'], item['id'], item['type']
        
        if itype == 'file':
            html = get_movie_player(name, iid)
            push_file(f"watch/{iid}.html", html, f"Sync Movie: {name}")
            sync_data.append({"name": name, "url": f"watch/{iid}.html", "type": "Movie"})
        
        elif itype == 'folder':
            f_resp = requests.get(f"https://api.abyss.to/v1/resources?key={ABYSS_API_KEY}&parentId={iid}")
            child_items = f_resp.json().get('items', [])
            if child_items:
                episodes = [{"name": e['name'], "id": e['id']} for e in child_items]
                html = get_series_player(name, episodes)
                push_file(f"series/{iid}.html", html, f"Sync Series: {name}")
                sync_data.append({"name": name, "url": f"series/{iid}.html", "type": "Series"})
        
        time.sleep(1.5) # Anti-spam delay

    # GENERATE HOME PAGE (INDEX.HTML)
    cards = "".join([f'''<a href="{i['url']}" style="display:block;padding:15px;background:#1a1a2e;color:#a0a0ff;border-radius:10px;text-decoration:none;border:1px solid #333;margin-bottom:10px"><b>{i['name']}</b><br><small>{i['type']}</small></a>''' for i in sync_data])
    
    index_html = f"""<!DOCTYPE html><html><head><title>CineView</title><meta name="viewport" content="width=device-width,initial-scale=1.0"></head><body style="background:#0f0f1d;color:#fff;font-family:sans-serif;padding:20px"><h1 style="color:#a0a0ff;text-align:center">CINEVIEW</h1><div style="max-width:500px;margin:0 auto">{cards}</div></body></html>"""
    
    push_file("index.html", index_html, "Update Home Page")
    print("Done!")

if __name__ == "__main__":
    main()
