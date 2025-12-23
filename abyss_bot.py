import os
import requests
import base64
import json
import time

# --- CONFIGURATION ---
ABYSS_API_KEY = os.getenv("ABYSS_KEY")
GITHUB_TOKEN = os.getenv("GH_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")

def push_to_github(path, content, msg):
    """Pushes a file to GitHub via API"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get SHA if file exists
        r = requests.get(url, headers=headers)
        sha = r.json().get('sha') if r.status_code == 200 else None
        
        payload = {
            "message": msg,
            "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
        }
        if sha:
            payload["sha"] = sha
            
        res = requests.put(url, headers=headers, json=payload)
        print(f"   [GitHub API] {path} -> Status: {res.status_code}")
        return res.status_code
    except Exception as e:
        print(f"   [GitHub Error] Failed to push {path}: {str(e)}")
        return None

def main():
    print("--- SYNC START ---")
    
    if not ABYSS_API_KEY or not GITHUB_TOKEN:
        print("!!! ERROR: ABYSS_KEY or GH_TOKEN missing from Secrets.")
        return

    # 1. Fetch from Abyss
    print("Fetching data from Abyss...")
    try:
        api_url = f"https://api.abyss.to/v1/resources?key={ABYSS_API_KEY}&maxResults=100"
        response = requests.get(api_url, timeout=20)
        data = response.json()
        items = data.get('items', [])
        print(f"Found {len(items)} items.")
    except Exception as e:
        print(f"!!! Abyss Error: {str(e)}")
        return

    catalog = []

    # 2. Process Items
    for item in items:
        try:
            name = item.get('name', 'Unknown')
            iid = item.get('id')
            itype = item.get('type')
            
            if not iid:
                continue

            print(f"Syncing: {name}...")

            if itype == 'file':
                # Movie Player Page
                html = f"<html><body style='margin:0;background:#000'><iframe src='https://abyss.to/e/{iid}' width='100%' height='100%' frameborder='0' allowfullscreen></iframe></body></html>"
                push_to_github(f"watch/{iid}.html", html, f"Sync {name}")
                catalog.append({"name": name, "url": f"watch/{iid}.html"})
            
            elif itype == 'folder':
                # Series Folder Handling
                f_url = f"https://api.abyss.to/v1/resources?key={ABYSS_API_KEY}&parentId={iid}"
                f_res = requests.get(f_url, timeout=15).json()
                eps = f_res.get('items', [])
                if eps:
                    html = f"<html><body style='background:#111;color:#fff;font-family:sans-serif;padding:20px'><h2>{name}</h2><ul>"
                    for e in eps:
                        html += f"<li>{e.get('name')}</li>"
                    html += "</ul></body></html>"
                    push_to_github(f"series/{iid}.html", html, f"Sync {name}")
                    catalog.append({"name": name, "url": f"series/{iid}.html"})
            
            time.sleep(1)
        except Exception as e:
            print(f"!!! Error on item {name}: {str(e)}")

    # 3. Final Index Build
    if catalog:
        print("Building index.html...")
        links = "".join([f'<li><a href="{c["url"]}" style="color:cyan;text-decoration:none;font-size:1.2rem">{c["name"]}</a></li>' for c in catalog])
        index_html = f"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1.0'><title>CineView</title></head><body style='background:#0f0f1d;color:#fff;font-family:sans-serif;padding:20px'><h1>🎥 My Library</h1><ul>{links}</ul></body></html>"
        push_to_github("index.html", index_html, "Update Index")
    
    print("--- SYNC FINISHED ---")

if __name__ == "__main__":
    main()y></html>"
                push(f"watch/{iid}.html", html, f"Sync Movie: {name}")
                catalog.append({"name": name, "link": f"watch/{iid}.html", "type": "Movie"})
            
            elif itype == 'folder':
                # Fetch episodes for folder
                f_url = f"https://api.abyss.to/v1/resources?key={ABYSS_API_KEY}&parentId={iid}"
                f_resp = requests.get(f_url).json()
                eps = [{"name": e.get('name'), "id": e.get('id')} for e in f_resp.get('items', [])]
                
                if eps:
                    ep_js = json.dumps(eps)
                    html = f"<html><body style='background:#111;color:#fff'><h1>{name}</h1><iframe id='p' src='' width='100%' height='500px'></iframe><script>const E={ep_js};function play(i){{document.getElementById('p').src='https://abyss.to/e/'+E[i].id}}play(0);</script></body></html>"
                    push(f"series/{iid}.html", html, f"Sync Series: {name}")
                    catalog.append({"name": name, "link": f"series/{iid}.html", "type": "Series"})
            
            time.sleep(1) # Safety delay
        except Exception as e:
            print(f"Error processing item {name}: {e}")

    # Final Index Update
    print("Building index.html...")
    if catalog:
        links_html = "".join([f'<li><a href="{c["link"]}">{c["name"]}</a> ({c["type"]})</li>' for c in catalog])
        index_content = f"<!DOCTYPE html><html><body><h1>My Library</h1><ul>{links_html}</ul></body></html>"
        push("index.html", index_content, "Update Home Page")
        print("--- Sync Complete ---")
    else:
        print("No items to add to index.html")

if __name__ == "__main__":
    main()    api_url = f"https://api.abyss.to/v1/resources?key={ABYSS_API_KEY}&maxResults=100"
    
    try:
        response = requests.get(api_url)
        print(f"Abyss API Response Status: {response.status_code}")
        data = response.json()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to connect to Abyss: {e}")
        exit(1)

    items = data.get('items', [])
    if not items:
        print("Warning: No items found in your Abyss account.")
    
    catalog = []

    for item in items:
        name = item.get('name', 'Unknown')
        iid = item.get('id')
        itype = item.get('type')
        
        print(f"Processing: {name} ({itype})")
        
        try:
            if itype == 'file':
                html = f"<html><body style='margin:0;background:#000'><iframe src='https://abyss.to/e/{iid}' width='100%' height='100%' frameborder='0' allowfullscreen></iframe></body></html>"
                push(f"watch/{iid}.html", html, f"Sync Movie: {name}")
                catalog.append({"name": name, "link": f"watch/{iid}.html", "type": "Movie"})
            
            elif itype == 'folder':
                # Fetch episodes for folder
                f_url = f"https://api.abyss.to/v1/resources?key={ABYSS_API_KEY}&parentId={iid}"
                f_resp = requests.get(f_url).json()
                eps = [{"name": e.get('name'), "id": e.get('id')} for e in f_resp.get('items', [])]
                
                if eps:
                    ep_js = json.dumps(eps)
                    html = f"<html><body style='background:#111;color:#fff'><h1>{name}</h1><iframe id='p' src='' width='100%' height='500px'></iframe><script>const E={ep_js};function play(i){{document.getElementById('p').src='https://abyss.to/e/'+E[i].id}}play(0);</script></body></html>"
                    push(f"series/{iid}.html", html, f"Sync Series: {name}")
                    catalog.append({"name": name, "link": f"series/{iid}.html", "type": "Series"})
            
            time.sleep(1) # Safety delay
        except Exception as e:
            print(f"Error processing item {name}: {e}")

    # Final Index Update
    print("Building index.html...")
    if catalog:
        links_html = "".join([f'<li><a href="{c["link"]}">{c["name"]}</a> ({c["type"]})</li>' for c in catalog])
        index_content = f"<!DOCTYPE html><html><body><h1>My Library</h1><ul>{links_html}</ul></body></html>"
        push("index.html", index_content, "Update Home Page")
        print("--- Sync Complete ---")
    else:
        print("No items to add to index.html")

if __name__ == "__main__":
    main()            catalog.append({"name": name, "link": f"watch/{iid}.html", "type": "Movie"})
        
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
