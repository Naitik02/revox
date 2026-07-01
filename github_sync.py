import subprocess
import threading
import time
import os

SYNC_INTERVAL = 120  # Sync every 2 minutes

def auto_pull():
    token = os.environ.get("GITHUB_TOKEN")
    if token and os.path.exists('.git'):
        subprocess.run(["git", "config", "--global", "user.email", "bot@revox.com"], check=False)
        subprocess.run(["git", "config", "--global", "user.name", "Revox Bot"], check=False)
        
        result = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True)
        url = result.stdout.strip()
        if "github.com" in url and "@github.com" not in url:
            if url.startswith("https://"):
                auth_url = url.replace("https://github.com/", f"https://{token}@github.com/")
                subprocess.run(["git", "remote", "set-url", "origin", auth_url], check=False)

    if os.path.exists('.git'):
        print("🔄 Pulling latest database from GitHub...")
        subprocess.run(["git", "pull", "origin", "main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def sync_loop():
    while True:
        try:
            if os.path.exists('.git'):
                subprocess.run(["git", "add", "revox.db"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                result = subprocess.run(["git", "commit", "-m", "Auto Backup - DB Update"], capture_output=True, text=True)
                
                # If there were changes committed, push them!
                if "nothing to commit" not in result.stdout and "working tree clean" not in result.stdout:
                    print("🚀 Pushing database backup to GitHub...")
                    subprocess.run(["git", "push", "origin", "main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print("GitHub Sync Error:", e)
            
        time.sleep(SYNC_INTERVAL)

def start_github_sync():
    auto_pull()
    t = threading.Thread(target=sync_loop, daemon=True)
    t.start()
    print("✅ GitHub Live Auto-Sync Started (Every 2 mins)")
