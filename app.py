import os
import socket
from app import create_app

app = create_app()

# Enable SO_REUSEADDR untuk bisa reuse port
app.config['SERVER_NAME'] = None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Create socket dengan SO_REUSEADDR
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind(("0.0.0.0", port))
        sock.close()
        print(f"Port {port} tersedia, starting Flask app...")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
    except OSError as e:
        print(f"Port {port} tetap terpakai: {e}")
        print("Coba restart aplikasi di Delcom dashboard")
        exit(1)
