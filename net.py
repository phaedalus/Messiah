import socket
from config import LAN_MODE, PORT, MAX_MESSAGE_SIZE
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
                    conn.settimeout(10.0)
                    buf = b""

                    while True:
                        try:
                            chunk = conn.recv(4096)
                        except socket.timeout:
                            break
                        if not chunk:
                            break

                        buf += chunk
                        if len(buf) > MAX_MESSAGE_SIZE:
                            resp = handle_message('{"cmd"}:"_"')
                            conn.sendall((resp + "\n").encode("utf-8"))
                            buf = "b"
                            break

                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            if not line.strip():
                                continue
                            msg = line.decode("utf-8", errors="replace")
                            resp = handle_message(msg)
                            conn.sendall((resp + "\n").encode("utf-8"))

        except KeyboardInterrupt:
            print("\n[Messiah] spinning down.")