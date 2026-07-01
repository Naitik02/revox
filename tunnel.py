import subprocess
import re
import threading
import os

def start_tunnel(port):
    print("🌍 Requesting Public Internet Tunnel...")
    
    # Run SSH tunnel to localhost.run
    process = subprocess.Popen(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-R", f"80:localhost:{port}", "nokey@localhost.run", "-T"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    for line in iter(process.stdout.readline, ''):
        if "tunneled with tls termination" in line:
            # Extract URL
            match = re.search(r"https://[a-zA-Z0-9.-]+\.lhr\.life", line)
            if match:
                url = match.group(0)
                print("\n=======================================================")
                print("🌍 PUBLIC INTERNET URL (Access Anywhere in the World):")
                print(f"👉 {url}/")
                print("=======================================================\n")
                
                # Save it so bot.py can use it for the Admin Panel button!
                with open("public_url.txt", "w") as f:
                    f.write(f"{url}/")
                break

def launch(port):
    t = threading.Thread(target=start_tunnel, args=(port,), daemon=True)
    t.start()
