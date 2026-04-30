import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Delcom harus set PORT env var, jika tidak ada gunakan 3000
    port = int(os.environ.get("PORT", "3000"))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting Flask on {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
