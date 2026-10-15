"""A small TCP chat server: receive a message, type a reply, send it back."""

import argparse
import socket

MAX_BYTES = 8192


def handle_client(connection, address):
    """Chat with one client, each will take a turn until one disconects."""
    print(f"\nClient connected: {address[0]}:{address[1]}", flush=True)
    print("Type a reply after each message. /back disconnects; /quit stops the server.", flush=True)
    with connection.makefile("rb") as incoming:
        while True:
            # TCP is a byte stream. Read through the newline ending one message.
            raw = incoming.readline(MAX_BYTES + 1)
            if not raw:
                print("Client disconnected.", flush=True)
                return True
            if len(raw) > MAX_BYTES or not raw.endswith(b"\n"):
                print("Client sent an invalid or oversized message.", flush=True)
                return True
            message = raw.decode("utf-8").strip()
            if not message or len(message) > 2000:
                connection.sendall(b"Please send a message with 1-2000 characters.\n")
                continue
            print(f"\nClient > {message}", flush=True)
            while True:
                reply = input("Server > ").strip()
                if reply == "/quit":
                    return False
                if reply == "/back":
                    return True
                if 1 <= len(reply) <= 2000:
                    break
                print("Please type a reply with 1-2000 characters.", flush=True)
            # UTF-8 supports accented characters; the newline frames the reply.
            connection.sendall((reply + "\n").encode("utf-8"))


def main():
    """Listen address and serve one conversation at a time."""
    parser = argparse.ArgumentParser(description="ChatLink terminal TCP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be from 1 to 65535.")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((args.host, args.port))
            server.listen(1)
            print(f"\n  CHATLINK / TCP SERVER\n  Listening on {args.host}:{args.port}\n"
                  "  Keep this terminal open. Stop with Ctrl+C.\n", flush=True)
            running = True
            while running:
                print("Waiting for a client...", flush=True)
                connection, address = server.accept()
                with connection:
                    try:
                        running = handle_client(connection, address)
                    except (ConnectionError, UnicodeError, OSError) as exc:
                        print(f"Conversation ended: {exc}", flush=True)
    except (KeyboardInterrupt, EOFError):
        print("\nServer stopped.")
    except OSError as exc:
        parser.exit(1, f"Could not start the server: {exc}\n")


if __name__ == "__main__":
    main()
