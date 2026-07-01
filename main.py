import threading
import os
import github_sync
from bot import bot, expiry_checker_loop
from web import app

def run_bot():
    print("Starting Telegram Bot...")
    t = threading.Thread(target=expiry_checker_loop, daemon=True)
    t.start()
    bot.infinity_polling()

def run_web():
    port = int(os.environ.get("PORT", 5000))
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = "127.0.0.1"
    
    print(f"\n==============================================")
    print(f"📱 OPEN ADMIN PANEL ON YOUR LOCAL WI-FI:")
    print(f"👉 http://{ip}:{port}/")
    print(f"==============================================\n")
    
    import tunnel
    if not os.environ.get("RENDER"):
        tunnel.launch(port)
    
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    github_sync.start_github_sync()
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    run_web()
