import subprocess
import re
import threading
import os
import urllib.request

def start_tunnel(port):
    try:
        if not os.path.exists("cloudflared.exe"):
            print("🌍 Downloading Secure Cloudflare Tunnel (One-time)...")
            urllib.request.urlretrieve("https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe", "cloudflared.exe")
        
        print("🌍 Starting Global Cloudflare Tunnel...")
        
        # Run Cloudflare tunnel
        process = subprocess.Popen(
            ["cloudflared.exe", "tunnel", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            if "trycloudflare.com" in line:
                # Extract URL
                match = re.search(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", line)
                if match:
                    url = match.group(0)
                    print("\n=======================================================")
                    print("🌍 CLOUDFLARE SECURE URL (Access Anywhere globally):")
                    print(f"👉 {url}/")
                    print("=======================================================\n")
                    
                    # Save it so bot.py can use it for the Admin Panel button!
                    with open("public_url.txt", "w") as f:
                        f.write(f"{url}/")
                    break
    except Exception as e:
        print("Tunnel Error:", e)

def launch(port):
    t = threading.Thread(target=start_tunnel, args=(port,), daemon=True)
    t.start()
