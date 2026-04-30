import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Delcom akan set PORT environment variable, atau gunakan port 5000
    port = int(os.environ.get("PORT", 5000))
    try:
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
    except OSError:
        # Jika port terpakai, coba port lain
        print(f"Port {port} sudah terpakai, mencoba port {port+1}")
        app.run(host="0.0.0.0", port=port+1, debug=False, use_reloader=False, threaded=True)
