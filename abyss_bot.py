import os, requests, base64, json, time

# --- CONFIGURATION ---
ABYSS_API_KEY = os.getenv("ABYSS_KEY")
GITHUB_TOKEN = os.getenv("GH_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
USER_NAME = GITHUB_REPO.split('/')[0]
REPO_NAME = GITHUB_REPO.split('/')[1]

def push_file(path, content, msg):
    """Pushes a file to GitHub via API"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # Get SHA if file already exists
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    
    payload = {
        "message": msg,
        "content": base64.b64encode(content.encode()).decode()
    }
    if sha: payload["sha"] = sha
    
    res = requests.put(url, headers=headers, json=payload)
    print(f"[{res.status_code}] {path}")
    return res.status_code

def get_movie_player(name, iid):
    """HTML for Single Movies"""
    return f"""<!DOCTYPE html><html><head><title>{name}</title><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>body{{margin:0;background:#000;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden}}iframe{{width:100%;height:100%;border:none}}</style></head><body><iframe src="https://abyss.to/e/{iid}" allowfullscreen></iframe></body></html>"""

def get_series_player(name, episodes):
    """HTML for Series/Episodes"""
    ep_js = json.dumps(episodes)
    options = "".join([f'<option value="{i}">Episode {i+1}</option>' for i in range(len(episodes))])
    return f"""<!DOCTYPE html><html><head><title>{name}</title><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>body{{background:#111;color:#fff;font-family:sans-serif;margin:0}}.player-box{{width:100%;aspect-ratio:16/9;background:#000}}iframe{{width:100%;height:100%;border:none}}.info{{padding:20px}}select{{width:100%;padding:10px;background:#333;color:#fff;border:1px solid #555}}</style></head><body><div class="player-box"><iframe id="ep-frame" src="" allowfullscreen></iframe></div><div class="info"><h1>{name}</h1><select onchange="play(this.value)">{options}</select></div><script>const eps={ep_js};function play(i){{document.getElementById('ep-frame').src="https://abyss.to/e/"+eps[i].id}}window.onload=()=>play(0);</script></body></html>"""

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
