import os, requests, base64, json, time

# --- CONFIG ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")

def push_github(path, content, msg):
    """Safely pushes or updates a file on GitHub."""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Check for existing file to get its SHA (required for updating)
    try:
        r = requests.get(url, headers=headers)
        sha = r.json().get('sha') if r.status_code == 200 else None
    except:
        sha = None
    
    payload = {
        "message": msg,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
    }
    if sha:
        payload["sha"] = sha
    
    res = requests.put(url, headers=headers, json=payload)
    print(f"   [GitHub] {path} -> Status: {res.status_code}")
    return res.status_code

def main():
    print("--- STARTING REPAIR SYNC ---")
    
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing! Ensure ABYSS_KEY and GH_TOKEN are set.")
        return

    # 1. Fetch Resources from Abyss
    print("Fetching from Abyss API...")
    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        resp = requests.get(url, timeout=20)
        data = resp.json()
        items = data.get('items', [])
        print(f"Total items found: {len(items)}")
    except Exception as e:
        print(f"API Connection Error: {e}")
        return

    catalog = []

    # 2. Process Items
    for item in items:
        name = item.get('name', 'Untitled Video')
        iid = item.get('id')
        is_dir = item.get('isDir', False)
        
        if not iid: continue

        # The short.icu URL you mentioned
        embed_url = f"https://short.icu/{iid}"
        
        if not is_dir:
            # MOVIE: Create player file
            path = f"watch/{iid}.html"
            catalog.append({"name": name, "url": path, "type": "Movie"})
            
            html = f"<!DOCTYPE html><html><head><title>{name}</title><meta name='viewport' content='width=device-width,initial-scale=1.0'><style>body{{margin:0;background:#000;overflow:hidden}}iframe{{width:100vw;height:100vh;border:none}}</style></head><body><iframe src='{embed_url}' allowfullscreen></iframe></body></html>"
            push_github(path, html, f"Sync Movie: {name}")
            time.sleep(1) # Delay for stability
        else:
            # SERIES: Create folder index
            path = f"series/{iid}.html"
            catalog.append({"name": name, "url": path, "type": "Series"})
            
            # Fetch folder contents
            try:
                f_url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}"
                f_resp = requests.get(f_url, timeout=15).json()
                children = f_resp.get('items', [])
                ep_links = "".join([f'<li><a href="https://short.icu/{c.get("id")}" style="color:#a0a0ff">{c.get("name")}</a></li>' for c in children])
                
                html = f"<html><body style='background:#111;color:#fff;font-family:sans-serif;padding:20px'><h1>{name}</h1><ul>{ep_links if ep_links else '<li>No items</li>'}</ul><br><a href='../index.html' style='color:#fff'>Back</a></body></html>"
                push_github(path, html, f"Sync Series: {name}")
            except:
                print(f"Error fetching folder {name}")

    # 3. FORCE REBUILD INDEX.HTML
    print("Updating Homepage (index.html)...")
    list_items = "".join([f'<li><a href="{c["url"]}">{c["name"]}</a> <small style="opacity:0.5">({c["type"]})</small></li>' for c in catalog])
    
    index_html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CineView Library</title>
        <style>
            body {{ background:#0f0f1d; color:#fff; font-family:sans-serif; padding:20px; max-width:700px; margin:0 auto; }}
            h1 {{ color:#a0a0ff; text-align:center; border-bottom:1px solid #333; padding-bottom:15px; }}
            ul {{ list-style:none; padding:0; }}
            li {{ background:#1a1a2e; margin-bottom:10px; padding:15px; border-radius:10px; border:1px solid #333; display:flex; justify-content:space-between; align-items:center; }}
            a {{ color:#fff; text-decoration:none; font-weight:bold; flex-grow:1; }}
            li:hover {{ border-color:#a0a0ff; }}
        </style>
    </head>
    <body>
        <h1>🎥 CINEVIEW</h1>
        <ul>{list_items if list_items else '<li>No videos found in account.</li>'}</ul>
    </body>
    </html>"""
    
    push_github("index.html", index_html, f"Refresh Library: {len(catalog)} items")
    print("--- SYNC FINISHED ---")

if __name__ == "__main__":
    main()    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing! Ensure ABYSS_KEY and GH_TOKEN are set.")
        return

    # 1. Fetch Resources from Abyss
    print("Fetching from Abyss API...")
    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        resp = requests.get(url, timeout=20)
        data = resp.json()
        items = data.get('items', [])
        print(f"Total items found: {len(items)}")
    except Exception as e:
        print(f"API Connection Error: {e}")
        return

    catalog = []

    # 2. Process Items
    for item in items:
        name = item.get('name', 'Untitled Video')
        iid = item.get('id')
        is_dir = item.get('isDir', False)
        
        if not iid: continue

        # The short.icu URL you mentioned
        embed_url = f"https://short.icu/{iid}"
        
        if not is_dir:
            # MOVIE: Create player file
            path = f"watch/{iid}.html"
            catalog.append({"name": name, "url": path, "type": "Movie"})
            
            html = f"<!DOCTYPE html><html><head><title>{name}</title><meta name='viewport' content='width=device-width,initial-scale=1.0'><style>body{{margin:0;background:#000;overflow:hidden}}iframe{{width:100vw;height:100vh;border:none}}</style></head><body><iframe src='{embed_url}' allowfullscreen></iframe></body></html>"
            push_github(path, html, f"Sync Movie: {name}")
            time.sleep(1) # Delay for stability
        else:
            # SERIES: Create folder index
            path = f"series/{iid}.html"
            catalog.append({"name": name, "url": path, "type": "Series"})
            
            # Fetch folder contents
            try:
                f_url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}"
                f_resp = requests.get(f_url, timeout=15).json()
                children = f_resp.get('items', [])
                ep_links = "".join([f'<li><a href="https://short.icu/{c.get("id")}" style="color:#a0a0ff">{c.get("name")}</a></li>' for c in children])
                
                html = f"<html><body style='background:#111;color:#fff;font-family:sans-serif;padding:20px'><h1>{name}</h1><ul>{ep_links if ep_links else '<li>No items</li>'}</ul><br><a href='../index.html' style='color:#fff'>Back</a></body></html>"
                push_github(path, html, f"Sync Series: {name}")
            except:
                print(f"Error fetching folder {name}")

    # 3. FORCE REBUILD INDEX.HTML
    print("Updating Homepage (index.html)...")
    list_items = "".join([f'<li><a href="{c["url"]}">{c["name"]}</a> <small style="opacity:0.5">({c["type"]})</small></li>' for c in catalog])
    
    index_html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CineView Library</title>
        <style>
            body {{ background:#0f0f1d; color:#fff; font-family:sans-serif; padding:20px; max-width:700px; margin:0 auto; }}
            h1 {{ color:#a0a0ff; text-align:center; border-bottom:1px solid #333; padding-bottom:15px; }}
            ul {{ list-style:none; padding:0; }}
            li {{ background:#1a1a2e; margin-bottom:10px; padding:15px; border-radius:10px; border:1px solid #333; display:flex; justify-content:space-between; align-items:center; }}
            a {{ color:#fff; text-decoration:none; font-weight:bold; flex-grow:1; }}
            li:hover {{ border-color:#a0a0ff; }}
        </style>
    </head>
    <body>
        <h1>🎥 CINEVIEW</h1>
        <ul>{list_items if list_items else '<li>No videos found in account.</li>'}</ul>
    </body>
    </html>"""
    
    push_github("index.html", index_html, f"Refresh Library: {len(catalog)} items")
    print("--- SYNC FINISHED ---")

if __name__ == "__main__":
    main()found</li>"}</ul>
                    <br><a href="../index.html" style="color:#a0a0ff">Back to Library</a>
                </body>
                </html>"""
                push_github(file_path, html, f"Update Series: {name}")
            except:
                print(f"Failed to fetch folder: {name}")

    # 3. FORCE REFRESH INDEX.HTML
    # We do this every single time to ensure it is never outdated
    print("Force-building index.html...")
    
    list_items = ""
    for c in catalog:
        list_items += f"""
        <li>
            <a href="{c['url']}">{c['name']}</a>
            <span style="font-size:10px; background:#a0a0ff; color:#000; padding:2px 5px; border-radius:3px; margin-left:10px;">{c['type']}</span>
        </li>"""

    index_html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CineView Library</title>
        <style>
            body {{ background: #0f0f1d; color: #fff; font-family: sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }}
            h1 {{ color: #a0a0ff; text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ background: #1a1a2e; margin-bottom: 10px; padding: 15px; border-radius: 8px; border: 1px solid #333; display: flex; justify-content: space-between; align-items: center; }}
            a {{ color: #fff; text-decoration: none; font-weight: bold; flex-grow: 1; }}
            li:hover {{ border-color: #a0a0ff; }}
        </style>
    </head>
    <body>
        <h1>🎥 CINEVIEW</h1>
        <ul>{list_items if list_items else "<li>No videos found in Abyss account.</li>"}</ul>
        <div style="text-align:center; font-size:10px; opacity:0.3; margin-top:50px;">Synced via Abyss API</div>
    </body>
    </html>"""
    
    # We use a unique commit message to see it clearly in GitHub history
    status = push_github("index.html", index_html, f"Manual Refresh: {len(catalog)} items")
    print(f"Final Index Status: {status}")
    print("--- SYNC COMPLETE ---")

if __name__ == "__main__":
    main()        resp = requests.get(url)
        data = resp.json()
        items = data.get('items', [])
    except Exception as e:
        print(f"Abyss API Connection Error: {e}"); return

    # 2. Get existing files in GitHub to skip duplicates
    print("Scanning repository...")
    synced_ids = set()
    r_watch = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/watch", 
                           headers={"Authorization": f"token {GH_TOKEN}"})
    if r_watch.status_code == 200:
        synced_ids.update([f['name'].replace('.html', '') for f in r_watch.json()])

    catalog = []
    
    # 3. Process items based on isDir (folder) or not (file)
    for item in items:
        name, iid = item.get('name'), item.get('id')
        is_dir = item.get('isDir', False)
        
        if not iid: continue

        if not is_dir: # It's a Movie
            path = f"watch/{iid}.html"
            catalog.append({"name": name, "url": path, "type": "Movie"})
            if iid not in synced_ids:
                print(f"New Movie: {name}")
                # Embed URL based on your API docs usually follows abyss.to/e/{id}
                html = f"<html><body style='margin:0;background:#000'><iframe src='https://abyss.to/e/{iid}' width='100%' height='100%' frameborder='0' allowfullscreen></iframe></body></html>"
                push_github(path, html, f"Add Movie: {name}")
                time.sleep(1)
        
        else: # It's a Series (Folder)
            path = f"series/{iid}.html"
            catalog.append({"name": name, "url": path, "type": "Series"})
            # Check if we need to create series page
            r_series = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", 
                                   headers={"Authorization": f"token {GH_TOKEN}"})
            if r_series.status_code != 200:
                print(f"New Series: {name}")
                # Fetch children using folderId
                f_url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&folderId={iid}"
                f_resp = requests.get(f_url).json()
                children = f_resp.get('items', [])
                if children:
                    links = "".join([f"<li>{c['name']}</li>" for c in children])
                    html = f"<html><body style='background:#111;color:#fff;padding:20px'><h1>{name}</h1><ul>{links}</ul></body></html>"
                    push_github(path, html, f"Add Series: {name}")

    # 4. Refresh Homepage (Always include all files)
    print("Updating Homepage...")
    list_items = "".join([f'<li><a href="{c["url"]}">{c["name"]}</a> <small>({c["type"]})</small></li>' for c in catalog])
    index_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CineView Library</title>
        <style>
            body {{ background:#0f0f1d; color:#fff; font-family:sans-serif; padding:20px; }}
            ul {{ list-style:none; padding:0; }}
            li {{ background:#1a1a2e; margin-bottom:10px; padding:15px; border-radius:8px; border:1px solid #333; }}
            a {{ color:#a0a0ff; text-decoration:none; font-weight:bold; }}
        </style>
    </head>
    <body>
        <h1 style="text-align:center; color:#a0a0ff;">🎥 CINEVIEW</h1>
        <ul>{list_items}</ul>
    </body>
    </html>"""
    
    push_github("index.html", index_html, "Full Library Sync")
    print("--- SYNC COMPLETE ---")

if __name__ == "__main__":
    main()
