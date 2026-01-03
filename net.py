import socket
from config import LAN_MODE, PORT
from dispatcher import handle_message

def get_host():
    return "0.0.0.0" if LAN_MODE else "127.0.0.1"

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

def start_server():
    HOST = get_host()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        server.settimeout(1.0)

        host = get_lan_ip() if LAN_MODE else "127.0.0.1"
        mode = "LAN" if LAN_MODE else "LOCAL"

        if LAN_MODE:
            print(f"[Warning] Server is listening in LAN mode — ensure a trusted network.")

        print(f"[Messiah] awaiting client on ({mode}) {host}:{PORT}")

        try:
            while True:
                try:
                    conn, addr = server.accept()
                    if LAN_MODE:
                        print(f"[Messiah] connection from {addr[0]}:{addr[1]}")
                except socket.timeout:
                    continue

                with conn:
                    buffer = b""
                    MAX_MSG = 64 * 1024

                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break

                        buffer += chunk
                        if len(buffer) > MAX_MSG:
                            print("[Messiah] message too large, dropping connection")
                            buffer = b""
                            break

                        if b"\n" in buffer:
                            break

                    if not buffer:
                        continue

                    message = buffer.decode("utf-8", errors="replace").rstrip("\n")
                    response = handle_message(message)
                    conn.sendall((response + "\n").encode("utf-8"))

        except KeyboardInterrupt:
            print("\n[Messiah] spinning down.")