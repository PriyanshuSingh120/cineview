import os, requests, base64, json, time

# --- CONFIG ---
ABYSS_KEY = os.getenv("ABYSS_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO = os.getenv("GITHUB_REPOSITORY")

def push_github(path, content, msg):
    """Safely pushes a file to GitHub"""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # Check for existing file SHA
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    
    payload = {
        "message": msg,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
    }
    if sha: payload["sha"] = sha
    
    res = requests.put(url, headers=headers, json=payload)
    print(f"[{res.status_code}] {path}")
    return res.status_code

def main():
    print("--- SYNC STARTING ---")
    if not ABYSS_KEY or not GH_TOKEN:
        print("CRITICAL: Secrets missing!"); return

    # 1. Fetch Abyss Resources
    # Using your API docs: /v1/resources?key={apiKey}
    print("Fetching from Abyss...")
    try:
        url = f"https://api.abyss.to/v1/resources?key={ABYSS_KEY}&maxResults=100"
        resp = requests.get(url)
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
